import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger("llm_service")


@dataclass
class CachedTemplate:
    """Cached prompt template with store association."""
    store_id: int
    template_type: str
    messages: List[Tuple[str, str]]


class TemplateManager:
    """Manages prompt template retrieval and caching for LLM service."""
    
    DEFAULT_TEMPLATES: Dict[str, List[Tuple[str, str]]] = {
        "retrieve_or_respond": [
            ("system", "You are a helpful AI assistant. Given the user question, "
                      "decide if you need to search for more information. "
                      "Return JSON: {{\"action\":\"retrieve\", \"query\":\"<query>\"}} "
                      "or {{\"action\":\"clarify\", \"answer\":\"<response>\"}}"),
            ("user", "User question: {user_input}")
        ],
        "generate_answer": [
            ("system", "You are a helpful AI assistant. "
                      "Answer the user question based on the retrieved information.\n"
                      "USER QUESTION: {user_input}\n"
                      "INFORMATION: {retrieved_information}\n"
                      "CONTEXT: {context}"),
        ]
    }
    
    def __init__(self, retriever_service_url: str):
        self.retriever_service_url = retriever_service_url.rstrip("/")
        self._cache: Dict[Tuple[int, str], CachedTemplate] = {}
        
    def get_template(self, store_id: int, template_type: str) -> List[tuple[str, str]]:
        """Retrieve prompt template for given store_id and template_type."""
        cache_key = (store_id, template_type)
        if cache_key in self._cache:
            logger.info("TemplateManager: using cached template for store_id=%s, template_type=%s", store_id, template_type)
            return self._cache[cache_key].messages
        
        template = self._fetch_template(store_id, template_type)
        if template:
            self._cache[cache_key] = template
            return template.messages

        logger.warning(
            "TemplateManager: No template found for store_id=%s, template_type=%s. Using default.",
            store_id, template_type
        )
        return self.DEFAULT_TEMPLATES.get(template_type, [])
    
    def _fetch_template(self, store_id: int, template_type: str) -> Optional[CachedTemplate]:
        """Fetch template from retriever service by store_id and template_type."""
        try:
            response = httpx.get(
                f"{self.retriever_service_url}/templates",
                params={"store_id": store_id, "template_type": template_type},
                timeout=5.0
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                return None
            template_data = data[0]
            messages = [(msg["role"], msg["content"]) for msg in template_data["messages"]]
            
            return CachedTemplate(
                store_id=store_id,
                template_type=template_type,
                messages=messages
            )            
        except httpx.HTTPError as e:
            logger.error("TemplateManager: Error fetching template from retriever service: %s", e)
            return None
        
    def invalidate_cache(self, store_id: Optional[int] = None, template_type: Optional[str] = None) -> None:
        """Invalidate cached templates. If no args, clears entire cache."""
        if store_id is None and template_type is None:
            logger.info("TemplateManager: Invalidating entire template cache")
            self._cache.clear()
            return

        keys_to_remove = [
            key for key in self._cache
            if (store_id is None or key[0] == store_id) and
               (template_type is None or key[1] == template_type)
        ]
        for key in keys_to_remove:
            logger.info("TemplateManager: Invalidating cache for store_id=%s, template_type=%s", key[0], key[1])
            del self._cache[key]