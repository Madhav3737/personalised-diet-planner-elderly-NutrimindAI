import logging
import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.prompts.prompts import CHAT_PROMPT
from app.rag.rag_pipeline import RAGPipeline
from app.models.models import ChatHistory, Profile, MedicalHistory
from app.repositories.repositories import (
    ChatHistoryRepository, ProfileRepository, MedicalHistoryRepository
)

logger = logging.getLogger(__name__)

# Try importing openai
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.chat_repo = ChatHistoryRepository(db)
        self.profile_repo = ProfileRepository(db)
        self.med_repo = MedicalHistoryRepository(db)
        self.rag = RAGPipeline(settings.DOCUMENTS_DIR, settings.VECTOR_DB_DIR)

        # Initialize OpenAI Client
        self.client = None
        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.error(f"Error initializing OpenAI client in ChatService: {e}")

    async def get_history(self, user_id: int) -> List[ChatHistory]:
        return await self.chat_repo.get_by_user_id(user_id)

    async def chat(self, user_id: int, message: str) -> ChatHistory:
        # 1. Fetch user data
        profile = await self.profile_repo.get_by_user_id(user_id)
        meds = await self.med_repo.get_by_user_id(user_id)
        
        profile_summary = "None"
        diseases_summary = "None"
        if profile:
            profile_summary = f"Age: {profile.age}, Gender: {profile.gender}, Cuisine: {profile.regional_cuisine}, Budget: {profile.economic_condition}"
        if meds:
            med_dict = {k: v for k, v in meds.__dict__.items() if not k.startswith('_') and isinstance(v, bool) and v}
            diseases_summary = ", ".join(med_dict.keys()) or "None"

        # 2. Query RAG
        retrieved = self.rag.retrieve(message, k=3)
        context = "\n\n".join([f"Source: {c['source']}\n{c['text']}" for c in retrieved])

        # 3. Generate answer
        ai_response = None
        if self.client:
            try:
                ai_response = self._chat_with_llm(profile_summary, diseases_summary, context, message)
            except Exception as e:
                logger.error(f"OpenAI chat call failed: {e}. Using rule-based fallback.")
                
        if not ai_response:
            ai_response = self._chat_rule_based(profile_summary, diseases_summary, context, message)

        # 4. Save to db
        chat_entry = ChatHistory(
            user_id=user_id,
            message=message,
            response=ai_response,
            sender="USER"
        )
        created = await self.chat_repo.create(chat_entry)
        return created

    def _chat_with_llm(self, profile_str: str, diseases_str: str, context: str, message: str) -> str:
        prompt = f"""
USER PROFILE CONTEXT:
- Profile: {profile_str}
- Medical History: {diseases_str}

RETRIEVED CLINICAL GUIDELINES:
{context}

USER QUERY:
{message}
"""
        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": CHAT_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content

    def _chat_rule_based(self, profile_str: str, diseases_str: str, context: str, message: str) -> str:
        """Rules-based keyword matcher fallback for chatbot responses."""
        msg_lower = message.lower()
        disclaimer = "This recommendation is AI-generated and should not replace advice from a qualified healthcare professional.\n\n"
        
        if "diabetes" in msg_lower or "sugar" in msg_lower or "glucose" in msg_lower:
            return disclaimer + (
                "Regarding your query about diabetes: The dietary guidelines recommend focusing on complex carbohydrates "
                "with a low glycemic index, such as oats, ragi, jowar, and whole wheat. Restrict refined sugars, sweets, "
                "and high-GI foods like white bread and juices. Incorporate high-fiber green leafy vegetables and divide "
                "your food intake into 5-6 small, frequent meals to avoid sudden spikes and crashes in blood sugar levels."
            )
        elif "salt" in msg_lower or "hypertension" in msg_lower or "bp" in msg_lower or "blood pressure" in msg_lower:
            return disclaimer + (
                "Regarding blood pressure control: It is crucial to limit daily salt/sodium intake to less than 5g (approx. 1 teaspoon). "
                "Avoid pickles, papads, canned foods, salted snacks (namkeen), and deep-fried items. Increase potassium intake "
                "by including fresh vegetables and local fruits. Use heart-healthy cooking oils such as mustard, sunflower, "
                "or rice bran oil in moderation."
            )
        elif "kidney" in msg_lower or "renal" in msg_lower or "ckd" in msg_lower:
            return disclaimer + (
                "Regarding kidney disease: In early-to-moderate stages, protein intake must be restricted (approx. 0.6-0.8g/kg body weight). "
                "Limit sodium strictly. You may also need to restrict phosphorus-rich dairy/nuts and potassium-rich items "
                "(bananas, coconut water, citrus fruits) if your physician has advised so. Hydrate based on clinical advice."
            )
        elif "water" in msg_lower or "drink" in msg_lower or "dehydration" in msg_lower:
            return disclaimer + (
                "Regarding hydration: Elderly individuals have a reduced sensation of thirst, making dehydration common. "
                "Aim for 1.5 to 2.0 liters of fluids daily (6-8 cups) unless you have fluid restrictions from heart or kidney failure. "
                "Warm water, buttermilk, light soups, and fresh fruit slices are excellent ways to stay hydrated."
            )
        elif "recipe" in msg_lower or "how to make" in msg_lower or "cook" in msg_lower:
            return disclaimer + (
                "For healthy elderly cooking: Prioritize boiling, steaming, or dry baking. For example, to make a healthy **Ragi porridge**: "
                "Mix 2 tablespoons of ragi flour in 1 cup of water, cook on low flame while stirring to prevent lumps. Add a pinch of salt or "
                "a tiny amount of buttermilk. It is rich in calcium and low-GI, making it excellent for elderly digestion, bones, and diabetes."
            )
        else:
            return disclaimer + (
                "Thank you for your question. Based on general guidelines: Elderly diets should prioritize nutrient density, "
                "adequate hydration (1.5-2L/day), dietary fiber (25-30g) for healthy digestion, and sufficient calcium/vitamin D "
                "for bones. Please make sure to avoid deep-fried foods, excessive salt, and sugars. Let me know if you would like "
                "specific dietary advice about diabetes, blood pressure, or kidney health!"
            )
        
        # If we have some RAG context, append a small portion of it to help
        if context:
            return disclaimer + f"Here is some relevant context from the guidelines:\n\n{context[:300]}..."
