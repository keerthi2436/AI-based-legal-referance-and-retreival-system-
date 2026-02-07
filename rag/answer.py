     # rag/answer.py
# FULL updated RAG answer wrapper — debug-ready and robust.
# Features:
# - Strong system prompt forcing concise direct answers.
# - Auto-detects low-relevance retrieval and falls back to zero-shot LLM.
# - Supports both old openai (<1.0 ChatCompletion) and new openai>=1.0 clients.
# - Debug logging of top retrieved snippets and relevance heuristic.
# - answer_query(query, top_k, verbose, use_llm) supports toggles.

import os
import logging
import traceback
import time
import pprint
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

pp = pprint.PrettyPrinter(depth=2)

# Try to import openai (old or new)
try:
    import openai as _openai_pkg
except Exception:
    _openai_pkg = None

# For openai>=1.0, there may be an OpenAI client class
try:
    from openai import OpenAI as OpenAIClient  # type: ignore
except Exception:
    OpenAIClient = None

# --------------------
# Configuration (tune these)
# --------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Default model — change to one you have access to
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))
# Increase TOP_K and MAX_CHARS for debugging / better context (reduce later if costly)
TOP_K = int(os.getenv("RAG_TOP_K", "10"))
MAX_CHARS_FROM_DOCS = int(os.getenv("MAX_CHARS_FROM_DOCS", "6000"))
RAG_VERBOSE = os.getenv("RAG_VERBOSE", "0") == "1"

if OPENAI_API_KEY and _openai_pkg is None:
    logger.warning("OPENAI_API_KEY set but 'openai' package is not installed.")

if _openai_pkg is not None:
    try:
        version = getattr(_openai_pkg, "__version__", "unknown")
        logger.info(f"openai package detected: {version}")
    except Exception:
        pass

# If API key present, try to configure for older clients
if OPENAI_API_KEY and _openai_pkg is not None:
    try:
        if hasattr(_openai_pkg, "api_key"):
            _openai_pkg.api_key = OPENAI_API_KEY
    except Exception:
        pass

# --------------------
# Retriever shim (flexible)
# --------------------
def _try_get_retriever_functions():
    try:
        import rag.retriever as retriever_mod
    except Exception:
        try:
            from rag import retriever as retriever_mod
        except Exception:
            logger.info("Could not import rag.retriever module.")
            return None

    if hasattr(retriever_mod, "get_relevant_docs"):
        return lambda q, k=TOP_K: retriever_mod.get_relevant_docs(q, k)

    if hasattr(retriever_mod, "get_or_create_index"):
        def getter(q, k=TOP_K):
            idx = retriever_mod.get_or_create_index()
            for method in ("query", "search", "similarity_search", "get_top_k"):
                if hasattr(idx, method):
                    func = getattr(idx, method)
                    try:
                        res = func(q, k)
                        return _normalize_retriever_result(res)
                    except TypeError:
                        try:
                            res = func(q, k)
                            return _normalize_retriever_result(res)
                        except Exception as e:
                            logger.debug(f"retriever idx.{method} failed: {e}")
            # fallback: naive scan of idx.chunks
            try:
                chunks = getattr(idx, "chunks", []) or []
                results = []
                ql = q.lower()
                for c in chunks:
                    text = c.get("text") or c.get("content") or str(c)
                    score = 1.0 if ql in text.lower() else 0.0
                    results.append({"source": c.get("source", "unknown"), "text": text, "score": score})
                results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
                return results[:k]
            except Exception:
                return []
        return getter

    logger.info("retriever module found but no usable entrypoint.")
    return None


def _normalize_retriever_result(res):
    out = []
    try:
        if res is None:
            return []
        if isinstance(res, list):
            for item in res:
                # Handle tuple from HybridIndex: (score, dict)
                if isinstance(item, tuple) and len(item) >= 2:
                    score, real_item = item[0], item[1]
                    if isinstance(real_item, dict):
                        src = real_item.get("source") or real_item.get("filename") or "unknown"
                        txt = real_item.get("text") or real_item.get("content") or str(real_item)
                        out.append({"source": src, "text": txt, "score": score})
                    else:
                        out.append({"source": "unknown", "text": str(real_item), "score": score})
                    continue

                if isinstance(item, str):
                    out.append({"source": "unknown", "text": item, "score": None})
                elif isinstance(item, dict):
                    src = item.get("source") or item.get("filename") or (item.get("meta") or {}).get("source") or "unknown"
                    txt = item.get("text") or item.get("content") or item.get("page_content") or item.get("chunk") or str(item)
                    sc = item.get("score") or item.get("similarity") or None
                    out.append({"source": src, "text": txt, "score": sc})
                else:
                    # object with attributes
                    src = getattr(item, "source", None) or (getattr(item, "metadata", {}) or {}).get("source") if hasattr(item, "metadata") else None
                    txt = getattr(item, "text", None) or getattr(item, "page_content", None) or str(item)
                    sc = getattr(item, "score", None)
                    out.append({"source": src or "unknown", "text": txt, "score": sc})
            return out
        return [{"source": "unknown", "text": str(res), "score": None}]
    except Exception:
        logger.exception("Error normalizing retriever result")
        return [{"source": "unknown", "text": str(res), "score": None}]

# --------------------
# Context builder (concise)
# --------------------
def build_context_block(retrieved: List[Dict[str, Any]], query: str, max_chars=MAX_CHARS_FROM_DOCS):
    if not retrieved:
        return "", []
    pieces = []
    sources = []
    total = 0
    for i, r in enumerate(retrieved[:TOP_K]):
        text = (r.get("text") or "").strip()
        src = r.get("source") or "unknown"
        snippet = text[:700].strip()
        add = f"[{i+1}] Source: {src}\n{snippet}\n"
        ln = len(add)
        if total + ln > max_chars:
            remaining = max_chars - total
            if remaining <= 40:
                break
            add = add[:remaining]
            pieces.append(add)
            total += len(add)
            sources.append({"index": i+1, "source": src, "excerpt": snippet[:200]})
            break
        pieces.append(add)
        total += ln
        sources.append({"index": i+1, "source": src, "excerpt": snippet[:200]})
    context_text = "\n\n".join(pieces)
    header = f"Top {len(pieces)} retrieved passages for: {query}\n\n"
    return header + context_text, sources

# --------------------
# Stronger system prompt
# --------------------
# --------------------
# Stronger system prompts
# --------------------
SYSTEM_PROMPT_NORMAL = """You are a concise, accurate legal assistant for Indian law. Follow these rules:
1) First, provide a direct short answer (1–3 sentences) that directly addresses the user's question.
2) Then (only if helpful), provide a one-sentence explanation and a confidence note (high/moderate/low).
3) When supporting statements rely on local documents included in the Context, add a single inline citation like [Source: Indian-Penal-Code-1860.pdf] after the sentence using that source.
4) Never invent exact statutory numbers, case names, or citations unless the context provides them. If unsure, say "I could not find an exact citation in the provided documents — please verify."
5) Keep responses professional, brief, and accurate. Do not output raw retrieval scores or long dumps.
"""

SYSTEM_PROMPT_SUMMARY = """You are a legal research assistant creating a comprehensive summary.
1) Provide a structured, bullet-point summary.
2) Use **bold** for key terms followed immediately by the definition on the same line (e.g., "- **Term:** Definition").
3) Avoid creating separate lines for terms and definitions to keep the layout compact.
4) Use clear, short main headings.
5) Cite sources explicitly for each major point using [Source: ...].
6) Be clear, professional, and visually organized.
"""

SYSTEM_PROMPT_QUIZ = """You are a legal tutor.
1) Based on the user's query and the retrieved context, generate a relevant multiple-choice question (A, B, C, D) to test the user's understanding.
2) Do NOT answer the user's question directly. Instead, pose a challenge.
3) Provide the question first, then using a generic separater, provide the answer.
   Format:
   **Question:** [Question text]
   
   A) [Option A]
   B) [Option B]
   C) [Option C]
   D) [Option D]
   
   ---
   **Correct Answer:** [Option X]
   **Explanation:** [Brief explanation citing context if available]
"""

SYSTEM_PROMPT_ELI5 = """You are a helpful legal guide explaining things to a non-expert.
1) Simplify all legal jargon into plain, everyday language.
2) Use analogies if helpful.
3) Keep it accurate but accessible (Explain Like I'm 5).
4) Still base your explanation on the provided Context.
5) Cite sources normally using [Source: ...].
"""

SYSTEM_PROMPT_DRAFTING = """You are a legal drafter.
1) Based on the user's request and the retrieved context, draft a legal clause, letter, or document section.
2) Use professional, precise legal language.
3) Structure the draft clearly (e.g., "Clause 1: ...").
4) After the draft, provide a brief note explaining why you chose specific wording based on the context.
5) Cite sources if specific statutes influenced the drafting.
"""

SYSTEM_PROMPT_SUGGESTIONS = """You are a helpful assistant anticipating the user's next needs.
1) Read the User's Question and the Answer provided.
2) Generate 3 specific, logical follow-up questions.
3) Ensure questions deeply relate to the specific legal details discussed (e.g., punishment, exceptions, procedure).
4) Do NOT repeat the user's question.
"""

# --------------------
# LLM call (supports old and new openai SDK)
# --------------------
def call_openai_chat_short(query: str, context_block: str, max_tokens: int = 512, use_context: bool = True, system_prompt_override: str = None) -> str:
    """
    Call OpenAI to get a concise answer.
    - use_context=True -> include context_block in system message.
    - use_context=False -> call model zero-shot (no local doc context) with an adjusted system prompt.
    """
    if _openai_pkg is None:
        raise RuntimeError("openai package not installed")

    if use_context and context_block:
        sys_p = system_prompt_override if system_prompt_override else SYSTEM_PROMPT_NORMAL
        messages = [
            {"role": "system", "content": sys_p},
            {"role": "system", "content": "Context (local documents):\n" + context_block},
            {"role": "user", "content": f"Question: {query}\n\n(Follow the system instructions strictly)."}
        ]
    else:
        # Fallback for no context OR specific zero-shot tasks (like suggestions)
        if system_prompt_override:
            zs_prompt = system_prompt_override
        else:
            zs_prompt = (
                "You are a concise, accurate legal assistant for Indian law. The user asked a question but no local documents "
                "are available or they seemed irrelevant. Provide a short, cautious answer (1-3 sentences) from general legal knowledge. "
                "Avoid inventing statutory numbers or cases; if uncertain, say 'I could not verify this from local documents; please verify.'"
            )
        messages = [
            {"role": "system", "content": zs_prompt},
            {"role": "user", "content": f"Question: {query}\n\nPlease answer concisely."}
        ]

    # Try old-style ChatCompletion if available
    try:
        if hasattr(_openai_pkg, "ChatCompletion"):
            resp = _openai_pkg.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=OPENAI_TEMPERATURE,
                max_tokens=max_tokens,
                top_p=1.0
            )
            choices = resp.get("choices") or []
            if not choices:
                return "No response from language model."
            text = choices[0]["message"]["content"].strip()
            return text
    except Exception as e:
        logger.debug("Old openai.ChatCompletion path failed: %s", e, exc_info=True)

    # Try new OpenAI client path (openai>=1.0)
    try:
        client = None
        if OpenAIClient is not None:
            try:
                client = OpenAIClient(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else OpenAIClient()
            except Exception:
                try:
                    client = OpenAIClient()
                except Exception:
                    client = None

        if client is None and hasattr(_openai_pkg, "OpenAI"):
            try:
                client = _openai_pkg.OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else _openai_pkg.OpenAI()
            except Exception:
                try:
                    client = _openai_pkg.OpenAI()
                except Exception:
                    client = None

        if client is None:
            raise RuntimeError("OpenAI client unavailable in installed openai package")

        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=max_tokens,
            top_p=1.0
        )
        choices = getattr(resp, "choices", None) or resp.get("choices", [])
        if not choices:
            return "No response from language model."
        first = choices[0]
        if hasattr(first, "message") and hasattr(first.message, "content"):
            text = first.message.content
        elif isinstance(first, dict) and "message" in first and "content" in first["message"]:
            text = first["message"]["content"]
        else:
            text = str(first)
        return text.strip()
    except Exception as e:
        logger.exception("New OpenAI client path failed")
        if "AuthenticationError" in str(type(e).__name__) or "401" in str(e):
             return "Error: Invalid OpenAI API Key. Please check the .env file."
        raise

# --------------------
# Local fallback summarizer (concise)
# --------------------
def _local_concise_summary(retrieved: List[Dict[str, Any]], query: str, max_sentences: int = 4) -> str:
    if not retrieved:
        return "No documents found in the index. Please upload documents to data/docs/ and build the index."

    candidates = []
    for r in retrieved[:TOP_K]:
        text = (r.get("text") or "").strip()
        src = r.get("source") or "unknown"
        parts = [p.strip() for p in text.replace("\n", " ").split(". ") if p.strip()]
        for p in parts[:3]:
            sent = (p + ".") if not p.endswith(".") else p
            candidates.append((sent.strip(), src))

    query_terms = [t.lower() for t in query.split() if len(t) > 3]
    scored = []
    for sent, src in candidates:
        score = 0
        sl = sent.lower()
        for qt in query_terms:
            if qt in sl:
                score += 2
        score += min(2, len(sent.split()) / 20)
        scored.append((score, sent, src))

    scored.sort(key=lambda x: x[0], reverse=True)
    picked = []
    seen_text = set()
    for sct, sent, src in scored:
        plain = sent.strip()
        if plain in seen_text:
            continue
        seen_text.add(plain)
        picked.append((sent, src))
        if len(picked) >= max_sentences:
            break

    if not picked:
        first = retrieved[0].get("text", "")[:400].strip()
        return first + ("..." if len(first) >= 400 else "")

    lines = []
    for i, (sent, src) in enumerate(picked):
        if i == 0:
            lines.append(f"{sent.strip()} (Source: {src})")
        else:
            lines.append(sent.strip())
    return " ".join(lines)

# --------------------
# Debug helper: test OpenAI connectivity
# --------------------
def test_openai_conn() -> (bool, str):
    if _openai_pkg is None:
        return False, "openai package not installed"
    if not OPENAI_API_KEY:
        return False, "OPENAI_API_KEY not set in environment"
    try:
        if OpenAIClient is not None:
            client = OpenAIClient(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else OpenAIClient()
            resp = client.chat.completions.create(model=OPENAI_MODEL, messages=[{"role":"user","content":"Ping"}], max_tokens=10)
            return True, "OK (new client)"
        if hasattr(_openai_pkg, "ChatCompletion"):
            resp = _openai_pkg.ChatCompletion.create(model=OPENAI_MODEL, messages=[{"role":"user","content":"Ping"}], max_tokens=10)
            return True, "OK (old client)"
        return False, "openai installed but client interface not recognized"
    except Exception as e:
        return False, f"OpenAI call failed: {e}"

# --------------------
# Public API
# --------------------
# --------------------
# Public API
# --------------------
def answer_query(query: str, top_k: int = TOP_K, verbose: Optional[bool] = None, use_llm: Optional[bool] = None, mode: str = "Normal") -> str:
    """
    - query: user's question
    - top_k: number of retrieval results to fetch
    - verbose: if True, append a short sources list; default from RAG_VERBOSE env
    - use_llm: True to force LLM (requires OPENAI_API_KEY), False to force local fallback,
               None => default is determined by presence of OPENAI_API_KEY
    - mode: "Normal", "Summary", or "Quiz"
    """
    verbose_flag = RAG_VERBOSE if verbose is None else bool(verbose)
    use_llm_flag = bool(use_llm) if use_llm is not None else bool(OPENAI_API_KEY)

    q = (query or "").strip()
    if not q:
        return "Please ask a question."

    retriever = _try_get_retriever_functions()
    retrieved = []
    if retriever:
        try:
            raw = retriever(q, top_k)
            retrieved = _normalize_retriever_result(raw)
            # DEBUG: log top retrieved results (short)
            try:
                debug_list = [{"source": r.get("source"), "snippet": (r.get("text") or "")[:220]} for r in retrieved[:min(len(retrieved), 6)]]
                logger.info("RAG debug — top retrieved: %s", pp.pformat(debug_list))
            except Exception:
                logger.exception("Failed to log retrieved debug info")
        except Exception:
            logger.exception("Retriever error")
            retrieved = []
    else:
        logger.info("No retriever configured; proceeding without local context.")
        retrieved = []

    # Quick relevance heuristic: count query-term hits in each snippet
    use_context = True
    try:
        q_terms = [t.lower() for t in q.split() if len(t) > 3]
        if not q_terms:
            q_terms = [q.lower()]

        best_match = 0
        for r in retrieved[:top_k]:
            txt = (r.get("text") or "").lower()
            count = sum(txt.count(term) for term in q_terms)
            if count > best_match:
                best_match = count

        logger.info("RAG debug — best_match_term_count=%s for query='%s'", best_match, q)
        # If best_match is too low (e.g., <2), treat retrieved docs as irrelevant
        if best_match < 2:
            use_context = False
    except Exception:
        use_context = True

    context_block = ""
    sources_meta = []
    if retrieved and use_context:
        context_block, sources_meta = build_context_block(retrieved, q, max_chars=MAX_CHARS_FROM_DOCS)
    else:
        context_block = ""  # ensure no local context will be used

    # Select system prompt based on mode
    if mode == "Summary":
        sys_p = SYSTEM_PROMPT_SUMMARY
    elif mode == "Quiz":
        sys_p = SYSTEM_PROMPT_QUIZ
    elif mode == "ELI5":
        sys_p = SYSTEM_PROMPT_ELI5
    elif mode == "Drafting":
        sys_p = SYSTEM_PROMPT_DRAFTING
    else:
        sys_p = SYSTEM_PROMPT_NORMAL

    # If LLM path requested and available
    if use_llm_flag and OPENAI_API_KEY and _openai_pkg is not None:
        try:
            # OPTIMIZATION: Combine Answer + Suggestions in one call to reduce latency
            # We append a special instruction to the system prompt or query
            if mode in ["Normal", "ELI5", "Summary"]:
                combo_instruction = (
                    "\n\nIMPORTANT: After providing the answer, output the delimiter '|||SUGGESTIONS|||' "
                    "followed immediately by 3 specific, legally relevant follow-up questions separated by pipes (|). "
                    "Example: Answer text... |||SUGGESTIONS|||Question 1?|Question 2?|Question 3?"
                )
                # Temporarily modify the system prompt or just rely on the instruction being strong enough
                # We'll append it to the query to ensure it's seen last
                q_for_llm = f"{q}\n{combo_instruction}"
            else:
                q_for_llm = q

            reply_text = call_openai_chat_short(q_for_llm, context_block, max_tokens=1024, use_context=use_context, system_prompt_override=sys_p)
            
            suggestions = []
            final_content = reply_text

            if "|||SUGGESTIONS|||" in reply_text:
                parts = reply_text.split("|||SUGGESTIONS|||")
                final_content = parts[0].strip()
                if len(parts) > 1:
                    s_raw = parts[1].strip()
                    suggestions = [s.strip() for s in s_raw.split('|') if "?" in s][:3]
            
            # Post-processing for specific modes
            if mode == "Normal" and not suggestions: 
                 # Fallback trim for normal if suggestions weren't generated correctly (rare)
                 final_content = final_content.strip().split("\n\n")[0].strip()

            return {
                "content": final_content,
                "suggestions": suggestions,
                "sources": sources_meta
            }

        except Exception:
            logger.exception("OpenAI synth failed — falling back to local summary.")

    if use_llm_flag and not OPENAI_API_KEY:
        logger.warning("LLM was requested (use_llm=True) but OPENAI_API_KEY not set — using local fallback.")

    # Fallback: local concise summary
    concise = _local_concise_summary(retrieved, q, max_sentences=4)
    if verbose_flag and retrieved:
        src_lines = []
        for i, r in enumerate(retrieved[:top_k]):
            src = r.get("source") or f"source_{i+1}"
            excerpt = (r.get("text") or "")[:200].replace("\n", " ")
            src_lines.append(f"- {src}: {excerpt}...")
        concise = concise + "\n\nSources:\n" + "\n".join(src_lines)
    
    return {
        "content": concise,
        "suggestions": [],
        "sources": sources_meta
    }
