from flask import Blueprint, request, jsonify
from db.models import Report, ReportState, Role, User, JobRequest, Comment
from db.client import db_client
from middleware.auth import authenticate, check_roles
from json import loads, dumps

reports_bp = Blueprint('reports', __name__)

# TODO: Uncomment check_auth_stage()
@reports_bp.route('/create-report', methods=['POST'])
@authenticate()
# @check_auth_stage()
@check_roles([Role.RESEARCHER])
def create_report():
    user: User = request.user
    data = request.json
    content: str = data.get('content')
    request_id: str = data.get('request_id')

    r = Report(content=content, job_request_id=request_id, user=user, user_has_unread=False, org_has_unread=True, status=ReportState.SUBMITTED)

    try:
        db_client.session.add(r)
        db_client.session.commit()
    except:
        return jsonify({"error": "Error creating report"}), 400
    return jsonify({"message": "Report created"}), 200

@reports_bp.route('/accept-report', methods=['POST'])
@authenticate()
# @check_auth_stage()
@check_roles([Role.ORGANIZATION])
def accept_report():
    org: User = request.user
    data = request.json
    report_id: str = data.get('report_id')

    r = db_client.session.query(Report).filter_by(id=report_id).first()
    if not r or r.organization != org:
        return jsonify({"error": "Error finding report or invalid credentials"}), 404

    r.status = ReportState.ACCEPTED

    try:
        db_client.session.commit()
    except:
        return jsonify({"error": "Error accepting report"}), 400
    return jsonify({"message": "Report accepted"}), 200

@reports_bp.route('/reject-report', methods=['POST'])
@authenticate()
# @check_auth_stage()
@check_roles([Role.ORGANIZATION])
def reject_report():
    org: User = request.user
    data = request.json
    report_id: str = data.get('report_id')

    r = db_client.session.query(Report).filter_by(id=report_id).first()
    if not r or r.organization != org:
        return jsonify({"error": "Error finding report or invalid credentials"}), 404

    r.status = ReportState.REJECTED

    try:
        db_client.session.commit()
    except:
        return jsonify({"error": "Error rejecting report"}), 400
    return jsonify({"message": "Report rejected"}), 200

@reports_bp.route('/get-all', methods=['GET'])
@authenticate()
# @check_auth_stage()
@check_roles([Role.RESEARCHER, Role.ORGANIZATION])
def get_all():
    u: User = request.user
    
    if u.role == Role.RESEARCHER:
        reports = db_client.session.query(Report).filter_by(user_id=u.id).all()
        
        r = [{
                'id': _.id,
                'unread': _.user_has_unread,
                'status': _.status.value,
                'commentCount': len(db_client.session.query(Comment).filter_by(report_id=_.id).all()),
                'organization': _.job_request.organization.name,
                'logo': loads(_.job_request.organization.md)['logo_url'],
                'user': _.user.name
            } for _ in reports]
    
        return jsonify({"message": "Reports returned", "reports": r}), 200
    elif u.role == Role.ORGANIZATION:
        reports = db_client.session.query(Report).select_from(JobRequest).filter_by(organization_id=u.id).join(Report, Report.job_request_id == JobRequest.id).all()
        
        r = [{
                'id': _.id,
                'unread': _.org_has_unread,
                'status': _.status.value,
                'commentCount': len(db_client.session.query(Comment).filter_by(report_id=_.id).all()),
                'organization': _.job_request.organization.name,
                'logo': loads(_.job_request.organization.md)['logo_url'],
                'user': _.user.name
            } for _ in reports]
    
        return jsonify({"message": "Reports returned", "reports": r}), 200

@reports_bp.route('/get-by-id', methods=['GET'])
@authenticate()
# @check_auth_stage()
@check_roles([Role.RESEARCHER, Role.ORGANIZATION])
def get_by_id():
    u: User = request.user
    data = request.json
    report_id: str = data.get('report_id')
    
    if u.role == Role.RESEARCHER:
        r = db_client.session.query(Report).filter_by(id=report_id).first()

        if not r or r.user_id != u.id:
            return jsonify({"error": "Error finding report or invalid credentials"}), 404
        
        r = [{
                'id': _.id,
                'unread': _.user_has_unread,
                'status': _.status.value,
                'commentCount': len(db_client.session.query(Comment).filter_by(report_id=_.id).all()),
                'comments': [{'message': c.content, 'senderName': c.user.name, 'timestamp': c.created_at} for c in db_client.session.query(Comment).filter_by(report_id=_.id).all()],
                'organization': _.job_request.organization.name,
                'logo': loads(_.job_request.organization.md)['logo_url'],
                'user': _.user.name
            } for _ in [r]][0]
    
        return jsonify({"message": "Report returned", "report": r}), 200
    elif u.role == Role.ORGANIZATION:
        r = db_client.session.query(Report).filter_by(id=report_id).first()

        if not r or r.job_request.organization_id != u.id:
            return jsonify({"error": "Error finding report or invalid credentials"}), 404
        
        r = [{
                'id': _.id,
                'unread': _.org_has_unread,
                'status': _.status.value,
                'commentCount': len(db_client.session.query(Comment).filter_by(report_id=_.id).all()),
                'comments': [{'message': c.content, 'senderName': c.user.name, 'timestamp': c.created_at} for c in db_client.session.query(Comment).filter_by(report_id=_.id).all()],
                'organization': _.job_request.organization.name,
                'logo': loads(_.job_request.organization.md)['logo_url'],
                'user': _.user.name
            } for _ in [r]][0]
    
        return jsonify({"message": "Report returned", "report": r}), 200