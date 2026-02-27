@router.post("/")
def create_resource(request: Request, db: Session = Depends(get_db)):

    if "create_resource" not in request.state.permissions:
        raise HTTPException(status_code=403, detail="Forbidden")

    service = ResourceService(db)
    return service.create(request.state.org_id, ...)