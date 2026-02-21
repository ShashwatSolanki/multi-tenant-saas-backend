@router.get("/me")
def read_me(current_user = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "organization_id": str(current_user.organization_id)
    }