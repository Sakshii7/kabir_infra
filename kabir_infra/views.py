import xmlrpc.client

from django_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from kabir_infra_app.db_conn import DbConn
from utilis import Environment

url = Environment.get("HOST_URL")
db = Environment.get("DATABASE_NAME")
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))


@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    try:
        user_id = common.authenticate(db, username, password, {})
        user_details = DbConn().get('res.users', 'read', [[int(user_id)]],
                                    {'fields': ['name', 'partner_id', 'login']})[0]

        return Response(
            {'result': {"user_id": user_details["id"], "name": user_details["name"], "email": user_details["login"],
                        "partner_id": user_details["partner_id"],
                        'tokens': {
                            "access_token": create_access_token(
                                identity={'user_details': user_details, 'username': username}),
                            'refresh_token': create_refresh_token(
                                identity={'user_details': user_details, 'username': username})},
                        'status_code': status.HTTP_200_OK}})

    except Exception as e:
        return Response({"result": "Invalid Username or Password", "status_code": status.HTTP_204_NO_CONTENT})


@api_view(['GET'])
@jwt_required()
def my_profile(request):
    identity = get_jwt_identity(request)
    partner_id = identity["user_details"]["partner_id"][0]
    user_profile = DbConn().get('res.users', 'search_read', [[['partner_id', '=', int(partner_id)]]],
                                {'fields': ['name', 'father_name', 'code', 'mobile', 'email']})[0]
    return Response({'result': {'user_id': user_profile['id'], 'name': user_profile['name'],
                                'father_name': user_profile['father_name'], 'code': user_profile['code'],
                                'mobile': user_profile['mobile'], 'email': user_profile['email']}})


@api_view(['GET'])
@jwt_required()
def get_country_list(request):
    countries = DbConn().get('res.country', 'search_read', [[]],
                             {'fields': ['id', 'name']})
    return Response({'result': countries, 'status_code': status.HTTP_200_OK})


@api_view(['GET'])
@jwt_required()
def get_state_list(request):
    country_id = request.query_params.get("country_id")
    states = DbConn().get('res.country.state', 'search_read',
                          [[['country_id', '=', int(country_id)]]],
                          {'fields': ['id', 'name']})
    return Response({'result': states, 'status_code': status.HTTP_200_OK})


@api_view(['GET'])
@jwt_required()
def get_city_list(request):
    state_id = request.query_params.get("state_id")
    cities = DbConn().get('res.city', 'search_read', [[['state_id', '=', int(state_id)]]],
                          {'fields': ['id', 'name']})
    return Response({'result': cities, 'status_code': status.HTTP_200_OK})


@api_view(['GET'])
@jwt_required()
def get_site_list(request):
    sites = DbConn().get('syn.site', 'search_read', [[]],
                         {'fields': ['id', 'name']})
    return Response({'result': sites, 'status_code': status.HTTP_200_OK})


@api_view(['GET'])
@jwt_required()
def get_vendor_list(request):
    vendors = DbConn().get('syn.vendor', 'search_read', [[]],
                           {'fields': ['id', 'name']})
    return Response({'result': vendors, 'status_code': status.HTTP_200_OK})


@api_view(['GET'])
@jwt_required()
def grn_list(request):
    site_id = request.query_params.get("site_id")
    identity = get_jwt_identity(request)
    user_id = identity["user_details"]["id"]
    # print(payload)
    grn_details = DbConn().get('syn.grn', 'search_read', [[['create_uid', '=', int(user_id)],
                                                           ['site_id', '=', int(site_id)]]],
                               {'fields': ['name', 'company_id', 'vendor_id', 'site_id', 'purchase_order_id',
                                           'grn_date', 'vehicle_no', 'status']})
    for grn in grn_details:
        grn["grn_id"] = grn.pop("id")
        grn['status'] = str(grn["status"]).capitalize()
    return Response({'result': grn_details, 'status_code': status.HTTP_200_OK})


@api_view(['GET'])
@jwt_required()
def get_pending_purchase_order_list(request):
    site_id = request.query_params.get('site_id')
    identity = get_jwt_identity(request)
    user_id = identity["user_details"]["id"]
    purchase_order_details = DbConn().get('syn.purchase.order', 'search_read',
                                          [[['create_uid', '=', user_id], ['status', '=', 'approved'],
                                            ['site_id', '=', int(site_id)]]],
                                          {'fields': ['name', 'company_id', 'site_id', 'vendor_id', 'order_date',
                                                      'material_requisition_id', 'status']})
    for purchase_order in purchase_order_details:
        purchase_order["purchase_order_id"] = purchase_order.pop("id")
        purchase_order['status'] = str(purchase_order["status"]).capitalize()
    return Response({'result': purchase_order_details, 'status_code': status.HTTP_200_OK})


@api_view(['GET'])
@jwt_required()
def view_grn(request):
    grn_id = request.query_params.get("grn_id")
    grn_details = DbConn().get('syn.grn', 'read', [[int(grn_id)]],
                               {'fields': ['name', 'company_id', 'vendor_id', 'site_id', 'purchase_order_id',
                                           'grn_date', 'vehicle_no', 'status']})
    grn_lines = DbConn().get('syn.grn.line', 'search_read', [[["grn_id", "=", int(grn_id)]]],
                             {'fields': ['material_id', 'qty_received']})
    for line in grn_lines:
        line["grn_line_id"] = line.pop("id")
    for grn in grn_details:
        grn["grn_id"] = grn.pop("id")
        grn['grn_lines'] = grn_lines
        grn['status'] = str(grn["status"]).capitalize()
    return Response(
        {'result': grn_details, 'status_code': status.HTTP_200_OK})


@api_view(['GET'])
@jwt_required()
def view_purchase_order(request):
    purchase_order_id = request.query_params.get("purchase_order_id")
    purchase_order_details = DbConn().get('syn.purchase.order', 'read',
                                          [[int(purchase_order_id)]], {
                                              'fields': ['name', 'company_id', 'site_id', 'vendor_id',
                                                         'material_requisition_id', 'status']})
    purchase_order_lines = DbConn().get('syn.purchase.order.line', 'search_read',
                                        [[["purchase_order_id", "=", int(purchase_order_id)]]],
                                        {'fields': ['material_id', 'quantity', 'qty_received']})
    for material in purchase_order_lines:
        material_id = material.get("id")
        materials = DbConn().get('syn.material', 'search_read', [[['id', '=', material_id]]],
                                 {'fields': ['allowable_tolerance']})
    for line in purchase_order_lines:
        line["purchase_order_line_id"] = line.pop("id")
        # line["balance_qty"] = [line["quantity"] + material_tolerance / 100] + line["quantity"] - line["qty_received"]
    for purchase_order in purchase_order_details:
        purchase_order["purchase_order_id"] = purchase_order.pop("id")
        purchase_order['status'] = str(purchase_order["status"]).capitalize()
        purchase_order['purchase_order_lines'] = purchase_order_lines
    return Response(
        {'result': purchase_order_details, 'status_code': status.HTTP_200_OK})
