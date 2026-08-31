# User endpoints.
#
# Deliberately empty: there is no "list all users" endpoint — it would
# expose every registered user's email with no access control in front of
# it. Account creation happens via POST /api/auth/register, login via
# POST /api/auth/login; document/comment responses carry a denormalized
# *_name field (see models/document.py, models/review_comment.py) so the
# frontend never needs to fetch the full user list just to show a name.
