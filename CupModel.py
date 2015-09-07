from datetime import datetime

class Question:
    # source + "_" + id
    question_id =""
    question_title = ""
    question_content = ""
    link = ""
    up_votes = 0
    comment_count = 0
    raw_html = ""
    catagory = ""
    tags = []
    companies = []
    creation_date = datetime.fromordinal(1)