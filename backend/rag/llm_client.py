import google.generativeai as genai
from groq import Groq
from core.config import settings
from typing import Generator, AsyncGenerator
import logging
import asyncio
from rag.rate_limiter import with_rate_limit

logger = logging.getLogger(__name__)

# Initialize clients
groq_client = Groq(api_key=settings.GROQ_API_KEY)
genai.configure(api_key=settings.GEMINI_API_KEY)
_gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)


def generate(prompt: str, system: str = "") -> str:
    """
    Non-streaming generation.
    Tries Groq first. On any exception, falls back to Gemini.
    """
    try:
        response = groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.2
        )
        return response.choices[0].message.content

    except Exception as e:
        logger.warning(f"Groq failed: {e} — falling back to Gemini")
        try:
            full_prompt = f"{system}\n\n{prompt}" if system else prompt
            
            async def _call_gemini():
                return _gemini_model.generate_content(full_prompt).text
                
            try:
                loop = asyncio.get_running_loop()
                # If there's a running loop, run the coroutine in another thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return loop.run_in_executor(pool, lambda: asyncio.run(with_rate_limit(_call_gemini())))
            except RuntimeError:
                return asyncio.run(with_rate_limit(_call_gemini()))
        except Exception as e2:
            logger.error(f"Gemini also failed: {e2}")
            raise RuntimeError(f"Both LLMs failed. Groq: {e} | Gemini: {e2}")


def generate_stream(prompt: str, system: str = "") -> Generator[str, None, None]:
    """
    Streaming generation.
    Tries Groq streaming first. On any exception, falls back to Gemini streaming.
    """
    try:
        stream = groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.2,
            stream=True
        )
        for chunk in stream:
            text = chunk.choices[0].delta.content
            if text:
                yield text

    except Exception as e:
        logger.warning(f"Groq stream failed: {e} — falling back to Gemini stream")
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        
        async def _call_gemini_stream():
            # generate_content stream is a sync generator, so we can't 'await' it, 
            # we just call it and return it. But with_rate_limit awaits it...
            # Actually, with_rate_limit just awaits the execution of the call.
            return _gemini_model.generate_content(full_prompt, stream=True)
            
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                response = loop.run_in_executor(pool, lambda: asyncio.run(with_rate_limit(_call_gemini_stream())))
        except RuntimeError:
            response = asyncio.run(with_rate_limit(_call_gemini_stream()))
            
        for chunk in response:
            if chunk.text:
                yield chunk.text

async def generate_async(prompt: str, system: str = "") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, generate, prompt, system)

async def generate_stream_async(prompt: str, system: str = "") -> AsyncGenerator[str, None]:
    # This is a bit tricky to make properly async if the underlying client isn't async
    # For now, we'll just yield from a threadpool executor to unblock the event loop
    loop = asyncio.get_event_loop()
    
    # We fetch all chunks in a list to simplify async streaming if Groq's client is sync
    # Or just use the sync generator in a thread
    def get_chunks():
        return list(generate_stream(prompt, system))
        
    chunks = await loop.run_in_executor(None, get_chunks)
    for chunk in chunks:
        yield chunk
