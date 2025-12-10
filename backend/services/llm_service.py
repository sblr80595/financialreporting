# ============================================================================
# FILE: backend/services/llm_service.py
# ============================================================================
"""
LLM Service - Abstraction layer for multiple LLM providers.

Supports:
- Anthropic Claude (Sonnet 4.5)
- Google Gemini (2.5 Pro)
"""

from typing import Optional

from backend.config.settings import settings


class LLMService:
    """Service for generating content using different LLM providers."""

    @staticmethod
    def generate_content(system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Generate content using the configured LLM provider.

        Args:
            system_prompt: System instructions/prompt
            user_prompt: User message/prompt

        Returns:
            Generated content as string or None on error
        """
        provider = settings.LLM_PROVIDER.lower()

        print(f"🤖 Using LLM Provider: {provider.upper()}")

        if provider == "anthropic":
            return LLMService._generate_with_anthropic(system_prompt, user_prompt)
        elif provider == "gemini":
            return LLMService._generate_with_gemini(system_prompt, user_prompt)
        else:
            print(f"❌ Unknown LLM provider: {provider}")
            return None

    @staticmethod
    def _generate_with_anthropic(system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Generate content using Anthropic Claude.

        Args:
            system_prompt: System instructions
            user_prompt: User message

        Returns:
            Generated content or None
        """
        try:
            from anthropic import Anthropic

            # Validate API key
            if not settings.ANTHROPIC_API_KEY:
                print("❌ Error: ANTHROPIC_API_KEY not configured")
                return None

            # Initialize Anthropic client
            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

            print(f"   Model: {settings.ANTHROPIC_MODEL}")
            print(f"   System prompt length: {len(system_prompt)} chars")
            print(f"   User prompt length: {len(user_prompt)} chars")

            # Create message
            response = client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=16000,  # Claude Sonnet 4.5 supports large outputs
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            # Extract text from response
            if response.content and len(response.content) > 0:
                result = response.content[0].text
                print(f"   ✅ Generated {len(result)} characters")
                return result
            else:
                print("   ❌ No content in response")
                return None

        except Exception as e:
            print(f"❌ Error generating with Anthropic: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def _generate_with_gemini(system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Generate content using Google Gemini.

        Args:
            system_prompt: System instructions
            user_prompt: User message

        Returns:
            Generated content or None
        """
        try:
            import google.generativeai as genai

            # Validate API key
            if not settings.GEMINI_API_KEY:
                print("❌ Error: GEMINI_API_KEY not configured")
                return None

            # Configure Gemini
            genai.configure(api_key=settings.GEMINI_API_KEY)

            print(f"   Model: {settings.GEMINI_MODEL}")
            print(f"   System prompt length: {len(system_prompt)} chars")
            print(f"   User prompt length: {len(user_prompt)} chars")

            # Create model with system instruction
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction=system_prompt
            )

            # Generate content
            response = model.generate_content(user_prompt)

            if response.text:
                result = response.text
                print(f"   ✅ Generated {len(result)} characters")
                return result
            else:
                print("   ❌ No content in response")
                return None

        except Exception as e:
            print(f"❌ Error generating with Gemini: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_provider_info() -> dict:
        """
        Get information about the current LLM provider configuration.

        Returns:
            Dictionary with provider information
        """
        provider = settings.LLM_PROVIDER.lower()

        info = {
            "provider": provider,
            "available_providers": ["anthropic", "gemini"]
        }

        if provider == "anthropic":
            info.update({
                "model": settings.ANTHROPIC_MODEL,
                "api_key_configured": bool(settings.ANTHROPIC_API_KEY),
                "api_key_length": len(settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else 0
            })
        elif provider == "gemini":
            info.update({
                "model": settings.GEMINI_MODEL,
                "api_key_configured": bool(settings.GEMINI_API_KEY),
                "api_key_length": len(settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else 0
            })

        return info