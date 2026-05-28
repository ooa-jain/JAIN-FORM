from datetime import datetime

class Response:
    @staticmethod
    def _db():
        from app import db; return db

    @staticmethod
    def create(form_id, data, respondent_ip='', user_id=None):
        doc = {'form_id':str(form_id),'data':data,
               'respondent_ip':respondent_ip,'user_id':user_id,
               'submitted_at':datetime.utcnow()}
        r = Response._db().responses.insert_one(doc)
        return str(r.inserted_id)

    @staticmethod
    def get_by_form(form_id):
        return list(Response._db().responses.find(
            {'form_id':str(form_id)}).sort('submitted_at',-1))

    @staticmethod
    def get_count(form_id):
        return Response._db().responses.count_documents({'form_id':str(form_id)})

    @staticmethod
    def delete_all(form_id):
        Response._db().responses.delete_many({'form_id':str(form_id)})
