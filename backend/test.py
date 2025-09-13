from app.services.llm_service import get_llm

llm = get_llm()
resp = llm.invoke("Generate one Python interview question.")
print("LLM Direct Response:", resp)
