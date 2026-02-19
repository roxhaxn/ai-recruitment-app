# hr_dashboard/ahp_weights.py

def get_role_weights(role):
    """
    Return AHP weights for the selected job role.
    Sum of weights = 1
    """
    role = role.lower()
    if role == "data analyst":
        return {"Experience": 0.2, "Skills": 0.6, "Education": 0.2}
    elif role == "software engineer":
        return {"Experience": 0.3, "Skills": 0.5, "Education": 0.2}
    elif role == "project manager":
        return {"Experience": 0.5, "Skills": 0.3, "Education": 0.2}
    elif role == "ui/ux designer":
        return {"Experience": 0.2, "Skills": 0.6, "Education": 0.2}
    elif role == "marketing executive":
        return {"Experience": 0.3, "Skills": 0.4, "Education": 0.3}
    elif role == "business analyst":
        return {"Experience": 0.3, "Skills": 0.5, "Education": 0.2}
    else:
        # default equal weights
        return {"Experience": 0.33, "Skills": 0.33, "Education": 0.34}
