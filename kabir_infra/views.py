import random
import xmlrpc.client
from datetime import datetime, timedelta

from django_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from kabir_infra_app.db_conn import DbConn
from utils import Environment, Models, Common

url = Environment.get("HOST_URL")
db = Environment.get("DATABASE_NAME")
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))


# Login Api
@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    try:
        user_id = common.authenticate(db, username, password, {})
        user_details = DbConn().get(Models.user, 'read', [[int(user_id)]],
                                    {'fields': ['name', 'partner_id', 'login']})
        app_role = get_app_role(user_id)
        for user in user_details:
            user["user_id"] = user.pop("id")
            user["email"] = user.pop("login")
            user["app_role"] = app_role
        return Response(
            {'result': user_details,
             'tokens': {
                 "access_token": create_access_token(identity={'user_details': user_details, 'username': username}),
                 'refresh_token': create_refresh_token(identity={'user_details': user_details, 'username': username})},
             'status_code': status.HTTP_200_OK})
    except Exception:
        return Response({"result": "invalid username or password", "status_code": status.HTTP_400_BAD_REQUEST},
                        status=status.HTTP_400_BAD_REQUEST)


# For getting the App Role of the User.
def get_app_role(user_id):
    category_id = DbConn().get(Models.groups, 'search', [[['category_id', "like", 'Construction Site Management']]])
    app_role = ''
    if category_id:
        get_admin_group_id = DbConn().get(Models.groups, 'search_read', [[['name', 'like', 'Administrator']]],
                                          {'fields': ['users']})
        get_supervisior_group_id = DbConn().get(Models.groups, 'search_read', [[['name', 'like', 'Site Supervisor']]],
                                                {'fields': ['users']})
        if int(user_id) in get_admin_group_id[0].get("users"):
            app_role = "admin"
        elif int(user_id) in get_supervisior_group_id[0].get("users"):
            app_role = "supervisior"
        else:
            app_role
    return app_role


# Refresh Token Api.
@api_view(['GET'])
@jwt_required(refresh=True)
def refresh_token(request):
    identity = get_jwt_identity(request)
    return Response({"access_token": create_access_token(identity)})


# Generating the OTP after the user forget their password.
@api_view(["GET"])
def forget_password(request):
    username = request.query_params.get('username')
    user_details = DbConn().get(Models.user, 'search_read', [[['login', '=', username]]], {'fields': ['partner_id']})
    if user_details:
        user_id = user_details[0]["id"]
        partner_id = user_details[0]["partner_id"][0]
        current_time = datetime.now()
        string = current_time.strftime("%Y-%m-%d %H:%M:%S")
        otp_time = Common.convert_local_time_to_utc(string)
        otp = random.randint(1000, 9999)
        DbConn().get(Models.partner, 'write', [[partner_id], {'otp': otp, 'otp_time': otp_time, 'otp_flag': False}])
        return Response({'result': {'otp': otp, 'user_id': user_id,
                                    'msg': 'A 4 digit OTP is sent to your registered mobile number'},
                         'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)
    else:
        return Response({'result': 'user does not exist.',
                         'status_code': status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)


# Api for Match the OTP, Check the Expiration Time and Check if the OTP is already used or not.
@api_view(['POST'])
def check_otp(request):
    otp = request.data.get('otp')
    user_id = request.data.get('user_id')
    user_details = DbConn().get(Models.user, 'search_read', [[['id', '=', int(user_id)]]], {'fields': ['partner_id']})
    partner_id = user_details[0]['partner_id'][0]
    otp_match = DbConn().get(Models.partner, 'search_read', [[['otp', '=', int(otp)]]],
                             {'fields': ['otp_time', 'otp_flag']})
    if otp_match:
        otp_time = otp_match[0]['otp_time']
        otp_flag = otp_match[0]['otp_flag']
        converted_time = Common.convert_utc_to_local_time(otp_time)
        local_time = datetime.strptime(converted_time, "%Y-%m-%d %H:%M:%S")
        current_time = datetime.now()
        expire_time = local_time + timedelta(minutes=15)
        if otp_match and current_time > expire_time:
            return Response({'result': 'otp time expires', 'status_code': status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)
        elif otp_match and current_time < expire_time and otp_flag is True:
            return Response({'result': 'otp is already used', 'status_code': status.HTTP_400_BAD_REQUEST},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            DbConn().get(Models.partner, 'write', [[partner_id], {'otp_flag': True}])
            return Response({'result': 'otp matched', 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)
    else:
        return Response({'result': 'otp does not exist',
                         'status_code': status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)


# Api for reset the User's Login Password.
@api_view(['POST'])
def reset_password(request):
    new_password = request.data.get('new_password')
    user_id = request.data.get('user_id')
    try:
        DbConn().get(Models.user, 'write', [[int(user_id)], {'password': new_password}])
        return Response({'result': 'password reset successfully', 'status_code': status.HTTP_200_OK},
                        status=status.HTTP_200_OK)
    except Exception:
        return Response({"result": "user does not exist", "status_code": status.HTTP_400_BAD_REQUEST},
                        status=status.HTTP_400_BAD_REQUEST)


# logged in User Profile Api.
@api_view(['GET'])
@jwt_required()
def user_profile(request):
    identity = get_jwt_identity(request)
    partner_id = identity["user_details"][0]["partner_id"][0]
    user_details = DbConn().get(Models.user, 'search_read', [[['partner_id', '=', int(partner_id)]]],
                                {'fields': ['name', 'father_name', 'code', 'mobile', 'email']})
    for user in user_details:
        user["user_id"] = user.pop("id")
    return Response({'result': user_details, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


# Api for getting the Country List.
@api_view(['GET'])
@jwt_required()
def get_country_list(request):
    countries = DbConn().get(Models.country, 'search_read', [[]], {'fields': ['id', 'name']})
    return Response({'result': countries, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


# Api for getting the State List according to the Country id.
@api_view(['GET'])
@jwt_required()
def get_state_list(request):
    country_id = request.query_params.get("country_id")
    states = DbConn().get(Models.state, 'search_read', [[['country_id', '=', int(country_id)]]],
                          {'fields': ['id', 'name']})
    return Response({'result': states, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


# Api for getting the City List according to the State id.
@api_view(['GET'])
@jwt_required()
def get_city_list(request):
    state_id = request.query_params.get("state_id")
    cities = DbConn().get(Models.city, 'search_read', [[['state_id', '=', int(state_id)]]],
                          {'fields': ['id', 'name']})
    return Response({'result': cities, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


# Api for getting the Material List.
@api_view(['GET'])
@jwt_required()
def get_material_list(request):
    materials = DbConn().get(Models.materials, 'search_read', [[]],
                             {'fields': ['id', 'name', 'uom_id', 'allowable_tolerance']})
    return Response({'result': materials, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


# Api for getting the Vendor List.
@api_view(['GET'])
@jwt_required()
def get_vendor_list(request):
    vendors = DbConn().get(Models.vendor, 'search_read', [[]], {'fields': ['id', 'name']})
    return Response({'result': vendors, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


# Api for getting the Active Sites List.
@api_view(['GET'])
@jwt_required()
def get_active_site_list(request):
    sites = DbConn().get(Models.site, 'search_read', [[['status', '=', 'inprogress']]],
                         {'fields': ['name', 'shape_paths']})
    for site in sites:
        site["site_id"] = site.pop("id")
        shape_path = site["shape_paths"]
        if shape_path:
            shape = eval(shape_path.replace('\\', ''))
            site["shape_paths"] = shape
    return Response({'result': sites, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


# Api for getting the Grn List.
@api_view(['GET'])
@jwt_required()
def get_grn_list(request):
    site_id = request.query_params.get("site_id")
    identity = get_jwt_identity(request)
    user_id = identity["user_details"][0]["user_id"]
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    app_role = request.query_params.get("app_role")
    search_domain = [['site_id', '=', int(site_id)]]
    if app_role == 'admin':
        search_domain
    else:
        search_domain.append(['create_uid', '=', int(user_id)])
    if date_from and not date_to:
        search_domain.append(['grn_date', '>=', date_from])
    elif date_to and not date_from:
        search_domain.append(['grn_date', '<=', date_to])
    elif date_from and date_to:
        search_domain.append(['grn_date', '>=', date_from])
        search_domain.append(['grn_date', '<=', date_to])
    else:
        search_domain
    grn_list = DbConn().get(Models.grn, 'search_read', [search_domain],
                            {'fields': ['name', 'vendor_id', 'grn_date']})
    for grn in grn_list:
        grn["grn_id"] = grn.pop("id")
        grn["grn_date"] = Common.change_date_format(grn["grn_date"])
    return Response({'result': grn_list, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


# Api for Viewing the Particular Grn.
@api_view(['GET'])
@jwt_required()
def view_grn(request):
    grn_id = request.query_params.get("grn_id")
    grn_details = DbConn().get(Models.grn, 'read', [[int(grn_id)]],
                               {'fields': ['name', 'company_id', 'vendor_id', 'site_id', 'purchase_order_id',
                                           'grn_date', 'vehicle_no', 'status']})
    grn_lines = DbConn().get(Models.grn_line, 'search_read', [[["grn_id", "=", int(grn_id)]]],
                             {'fields': ['material_id', 'qty_received', 'uom_id']})
    for line in grn_lines:
        line["grn_line_id"] = line.pop("id")
    for grn in grn_details:
        grn["grn_id"] = grn.pop("id")
        grn['grn_lines'] = grn_lines
        grn['status'] = str(grn["status"]).capitalize()
        grn["grn_date"] = Common.change_date_format(grn["grn_date"])
    return Response(
        {'result': grn_details, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


# Api for getting purchase order list according to Site and Vendor id.
@api_view(['GET'])
@jwt_required()
def ref_purchase_order_list(request):
    site_id = request.query_params.get('site_id')
    vendor_id = request.query_params.get('vendor_id')
    purchase_order_list = DbConn().get(Models.purchase_order, 'search_read',
                                       [[['site_id', '=', int(site_id)], ['vendor_id', '=', int(vendor_id)],
                                         ['status', '=', 'approved']]],
                                       {'fields': ['name', 'site_id', 'vendor_id']})
    for purchase_order in purchase_order_list:
        purchase_order_lines = DbConn.get(Models.purchase_order_line, 'search_read',
                                          [[['purchase_order_id', '=', purchase_order.get('id')]]],
                                          {'fields': ['material_id', 'uom_id', 'quantity', 'qty_received']})
        purchase_order['purchase_order_id'] = purchase_order.pop('id')
        filtered_po_lines = []
        for po_line in purchase_order_lines:
            if po_line['qty_received'] < po_line['quantity']:
                filtered_po_lines.append(po_line)
            po_line['po_line_id'] = po_line.pop('id')
        purchase_order['po_lines'] = filtered_po_lines
    return Response({'result': purchase_order_list, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


# Api for Adding the Grn.
@api_view(['POST'])
@jwt_required()
def add_grn(request):
    site_id = request.data.get('site_id')
    vendor_id = request.data.get('vendor_id')
    purchase_order_id = request.data.get('purchase_order_id')
    vehicle_no = request.data.get('vehicle_no')
    document_no = request.data.get('document_no')
    po_line_id = request.data.get('po_line_id')
    qty_received = request.data.get('qty_received')
    document_date = request.data.get('document_date')
    grn_id = DbConn().get(Models.grn, 'create', [
        {'site_id': int(site_id), 'vendor_id': int(vendor_id), 'purchase_order_id': int(purchase_order_id),
         'vehicle_no': vehicle_no, 'document_no': document_no, 'document_date': document_date}])
    grn_details = DbConn().get(Models.grn, 'read', [[grn_id]],
                               {'fields': ['site_id', 'vendor_id', 'purchase_order_id', 'vehicle_no']})
    po_line_details = DbConn().get(Models.purchase_order_line, 'read', [[int(po_line_id)]],
                                   {'fields': ['rate_per_uom', 'uom_id']})
    rate_per_uom = po_line_details[0]['rate_per_uom']
    uom_id = po_line_details[0]['uom_id'][0]
    grn_line_id = DbConn().get(Models.grn_line, 'create', [
        {'grn_id': grn_id, 'material_id': po_line_id, 'rate_per_uom': rate_per_uom, 'uom_id': uom_id,
         'qty_received': qty_received}])
    grn_lines = DbConn().get(Models.grn_line, 'read', [[grn_line_id]],
                             {'fields': ['material_id', 'rate_per_uom', 'uom_id', 'qty_received']})
    for grn in grn_details:
        grn["grn_id"] = grn.pop("id")
        grn['grn_lines'] = grn_lines
    for line in grn_lines:
        line['grn_line_id'] = line.pop("id")
    return Response({'result': grn_details, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


# Api for getting the Pending Purchase Order List.
@api_view(['GET'])
@jwt_required()
def get_pending_purchase_order_list(request):
    site_id = request.query_params.get('site_id')
    identity = get_jwt_identity(request)
    user_id = identity["user_details"][0]["user_id"]
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    domain = [['create_uid', '=', user_id], ['status', '=', 'approved'],
              ['site_id', '=', int(site_id)]]
    if date_from and not date_to:
        domain.append(['order_date', '>=', date_from])
    elif date_to and not date_from:
        domain.append(['order_date', '<=', date_to])
    elif date_from and date_to:
        domain.append(['order_date', '>=', date_from])
        domain.append(['order_date', '<=', date_to])
    else:
        domain
    purchase_order_details = DbConn().get(Models.purchase_order, 'search_read', [domain],
                                          {'fields': ['name', 'vendor_id', 'order_date', 'status']})
    for purchase_order in purchase_order_details:
        purchase_order["purchase_order_id"] = purchase_order.pop("id")
        purchase_order["order_date"] = Common.change_date_format(purchase_order["order_date"])
        purchase_order['status'] = str(purchase_order["status"]).capitalize()
    return Response({'result': purchase_order_details, 'status_code': status.HTTP_200_OK},
                    status=status.HTTP_200_OK)


# Api for the View of Particular Purchase Order and show the balance quantity after calculating the allowable tolerance.
@api_view(['GET'])
@jwt_required()
def view_purchase_order(request):
    purchase_order_id = request.query_params.get("purchase_order_id")
    purchase_order_details = DbConn().get(Models.purchase_order, 'read',
                                          [[int(purchase_order_id)]], {
                                              'fields': ['name', 'site_id', 'vendor_id', 'order_date', 'status']})
    purchase_order_lines = DbConn().get(Models.purchase_order_line, 'search_read',
                                        [[["purchase_order_id", "=", int(purchase_order_id)]]],
                                        {'fields': ['material_id', 'quantity', 'qty_received', 'uom_id']})
    for line in purchase_order_lines:
        line["purchase_order_line_id"] = line.pop("id")
        material_id = line["material_id"][0]
        materials = DbConn().get(Models.materials, 'read', [[material_id]], {'fields': ['allowable_tolerance']})
        allowable_tolerance = materials[0]['allowable_tolerance']
        calculation = line["quantity"] * allowable_tolerance / 100 + line["quantity"] - line["qty_received"]
        line["balance_qty"] = round(calculation)

    for purchase_order in purchase_order_details:
        purchase_order["purchase_order_id"] = purchase_order.pop("id")
        purchase_order['status'] = str(purchase_order["status"]).capitalize()
        purchase_order['purchase_order_lines'] = purchase_order_lines
    return Response(
        {'result': purchase_order_details, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


# Api for getting the Material Requisition List.
@api_view(['GET'])
@jwt_required()
def get_material_requisition_list(request):
    site_id = request.query_params.get('site_id')
    identity = get_jwt_identity(request)
    user_id = identity["user_details"][0]["user_id"]
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    app_role = request.query_params.get('app_role')
    domain = [['site_id', '=', int(site_id)]]
    if app_role == "admin":
        domain
    else:
        domain.append(['user_id', '=', int(user_id)])
    if date_from and not date_to:
        domain.append(['requisition_date', '>=', date_from])
    elif date_to and not date_from:
        domain.append(['requisition_date', '<=', date_to])
    elif date_from and date_to:
        domain.append(['requisition_date', '>=', date_from])
        domain.append(['requisition_date', '<=', date_to])
    else:
        domain
    material_requisition_list = DbConn().get(Models.material_requisition, 'search_read', [domain],
                                             {'fields': ['name', 'requisition_date']})
    for material_requisition in material_requisition_list:
        material_requisition['material_requisition_id'] = material_requisition.pop("id")
        material_requisition["requisition_date"] = Common.change_date_format(
            material_requisition["requisition_date"])
    return Response({'result': material_requisition_list, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


# Api for the View of the Particular Material Requisition.
@api_view(['GET'])
@jwt_required()
def view_material_requisition(request):
    material_requisition_id = request.query_params.get("material_requisition_id")
    material_requisition_details = DbConn().get(Models.material_requisition, 'read', [[int(material_requisition_id)]],
                                                {'fields': ['name', 'site_id', 'requisition_date', ]})
    material_requisition_lines = DbConn().get(Models.material_requisition_line, 'search_read',
                                              [[['material_requisition_id', '=', int(material_requisition_id)]]],
                                              {'fields': ['material_id', 'quantity', 'uom_id']})
    purchase_order_list = DbConn().get(Models.purchase_order, 'search_read',
                                       [[['material_requisition_id', '=', int(material_requisition_id)]]],
                                       {'fields': ['name']})

    for line in material_requisition_lines:
        line['line_id'] = line.pop("id")
        material_id = line["material_id"][0]
        po_list = []
        for po in purchase_order_list:
            po_id = po["id"]
            purchase_order_lines = DbConn().get(Models.purchase_order_line, 'search_read',
                                                [[["purchase_order_id", "=", po_id],
                                                  ['material_id', '=', material_id]]],
                                                {'fields': ['material_id', 'purchase_order_id']})
            if purchase_order_lines:
                po_list.append(po)
        line['po_list'] = po_list
    for purchase_order in purchase_order_list:
        purchase_order['purchase_order_id'] = purchase_order.pop("id")
    for material_requisition in material_requisition_details:
        material_requisition['material_requisition_id'] = material_requisition.pop("id")
        material_requisition['rqn_lines'] = material_requisition_lines
        material_requisition["requisition_date"] = Common.change_date_format(
            material_requisition["requisition_date"])

    return Response({'result': material_requisition_details, 'status_code': status.HTTP_200_OK},
                    status=status.HTTP_200_OK)


# Api for Adding the Material Requisition.
@api_view(['POST'])
@jwt_required()
def add_material_requisition(request):
    site_id = request.data.get('site_id')
    identity = get_jwt_identity(request)
    user_id = identity["user_details"][0]["user_id"]
    materials = request.data.get('materials')
    material_data = eval(materials.replace('\\', ''))
    material_requisition_id = DbConn().get(Models.material_requisition, 'create',
                                           [{'site_id': int(site_id), 'user_id': user_id}])
    for mat in material_data:
        mat['material_requisition_id'] = material_requisition_id
        DbConn().get(Models.material_requisition_line, 'create', [mat])
    material_requisition_details = DbConn().get(Models.material_requisition, 'read', [[material_requisition_id]],
                                                {'fields': ['name', 'site_id', 'requisition_date']})

    for material_requisition in material_requisition_details:
        material_requisition["material_requisition_id"] = material_requisition.pop("id")
        material_requisition['material_requisition_lines'] = material_data
        material_requisition["requisition_date"] = Common.change_date_format(
            material_requisition["requisition_date"])
    return Response({'result': material_requisition_details, 'status_code': status.HTTP_200_OK},
                    status=status.HTTP_200_OK)


# Api for getting the Company List.
@api_view(['GET'])
@jwt_required()
def get_company_list(request):
    companies = DbConn().get(Models.company, 'search_read', [[]], {'fields': ['id', 'name']})
    return Response({'result': companies, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


# Management Dashboard Api for getting the No. of Active Site List and Total Outstanding of the Grn List.
@api_view(['GET'])
@jwt_required()
def management_dashboard(request):
    company_id = request.query_params.get('company_id')
    active_sites = DbConn().get(Models.site, 'search_read',
                                [[['company_id', '=', int(company_id)], ['status', '=', 'inprogress']]],
                                {'fields': ['name', 'shape_paths']})
    total_outstanding = 0.0
    no_of_sites = len(active_sites)
    for site in active_sites:
        site_id = site["id"]
        shape_path = site["shape_paths"]
        if shape_path:
            shape = eval(shape_path.replace('\\', ''))
            site["shape_paths"] = shape
        due_amount = 0.0
        grn_list = DbConn().get(Models.grn, 'search_read', [[['site_id', '=', site_id], ['status', '=', 'approved']]],
                                {'fields': ['name', 'total_amount', 'amount_paid']})
        for grn in grn_list:
            total_amount = grn['total_amount']
            amount_paid = grn['amount_paid']
            calculation = total_amount - amount_paid
            due_amount += calculation
        site['due_amount'] = due_amount
        total_outstanding += due_amount
        site["site_id"] = site.pop("id")
    return Response(
        {'result': {'no_of_active_sites': no_of_sites, 'total_outstanding': total_outstanding, 'sites': active_sites},
         'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)
