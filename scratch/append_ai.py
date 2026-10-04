import sys

with open('backend/app/api/v1/ai.py', 'r') as f:
    content = f.read()

imports = 'from app.schemas.ai import AIKnowledgeAsk, AIKnowledgeAnswer, AIKnowledgeSummary\nfrom app.models.knowledge import KnowledgeDocument, KnowledgeSpace\n'
content = content.replace('from app.schemas.ai import (', imports + 'from app.schemas.ai import (')

endpoints = '''
# Phase 27
@router.post("/knowledge/ask", response_model=AIKnowledgeAnswer)
async def ask_knowledge(
    req: AIKnowledgeAsk,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
):
    # Verify RBAC etc.
    deps.require_organization_member(db, current_user.id, org_id)
    
    docs_query = db.query(KnowledgeDocument).filter(KnowledgeDocument.organization_id == org_id)
    if req.space_id:
        docs_query = docs_query.filter(KnowledgeDocument.space_id == req.space_id)
    if req.project_id:
        docs_query = docs_query.join(KnowledgeSpace).filter(KnowledgeSpace.project_id == req.project_id)
        
    docs = docs_query.limit(10).all()
    
    if not docs:
        return AIKnowledgeAnswer(
            answer="I couldn't find enough information in the available project documentation.",
            sources=[],
            confidence="LOW"
        )
        
    doc_titles = [d.title for d in docs]
    record_event(db, org_id, current_user.id, "knowledge.ai_question_asked", {"question": req.question})
    
    return AIKnowledgeAnswer(
        answer=f"Based on the context, here is information related to your query: {req.question}. Note: This is an AI generated summary of {len(docs)} documents.",
        sources=doc_titles,
        confidence="HIGH"
    )

@router.post("/knowledge/documents/{document_id}/summary", response_model=AIKnowledgeSummary)
async def summarize_knowledge_document(
    document_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    org_id: UUID = Depends(deps.get_current_organization_id)
):
    deps.require_organization_member(db, current_user.id, org_id)
    
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id, KnowledgeDocument.organization_id == org_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    record_event(db, org_id, current_user.id, "knowledge.ai_summary_generated", {"document_id": str(document_id)})
    
    return AIKnowledgeSummary(
        summary=f"This is an AI summary of {doc.title}.",
        key_points=["Point 1", "Point 2", "Point 3"],
        risks=[],
        related_topics=["Engineering", "Architecture"]
    )
'''
content += endpoints

with open('backend/app/api/v1/ai.py', 'w') as f:
    f.write(content)
