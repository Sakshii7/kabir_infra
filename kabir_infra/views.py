import xmlrpc.client

from django_jwt_extended import create_access_token, create_refresh_token, jwt_required
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from kabir_infra_app.db_conn import DbConn
from utilis import Environment

url = Environment.get("HOST_URL")
db = Environment.get("DATABASE_NAME")
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))


@api_view(['GET'])
def login(request):
    user_name = request.data.get('username')
    user_pass = request.data.get('password')
    try:
        user_id = common.authenticate(db, user_name, user_pass, {})
        user_details = DbConn().get('res.users', 'read', [[int(user_id)]],
                                    {'fields': ['name', 'partner_id']})[0]

        return Response({'result': {"user_id": user_details["id"], "name": user_details["name"],
                                    "partner_id": user_details["partner_id"],
                                    'tokens': {
                                        "access_token": create_access_token(
                                            identity={'user_details': user_details, 'username': user_name}),
                                        'refresh_token': create_refresh_token(
                                            identity={'user_details': user_details, 'username': user_name})},
                                    'status_code': status.HTTP_200_OK}})

    except:
        return Response({"msg": "Invalid Username or Password", "status_code": status.HTTP_204_NO_CONTENT})


@api_view(['GET'])
@jwt_required()
def country_list(request):
    countries = DbConn().get('res.country', 'search_read', [[]],
                             {'fields': ['id', 'name']})
    return Response({'result': countries, 'status_code': status.HTTP_200_OK})


@api_view(['GET'])
@jwt_required()
def state_list(request):
    country_id = request.data.get("country_id")
    states = DbConn().get('res.country.state', 'search_read',
                          [[['country_id', '=', int(country_id)]]],
                          {'fields': ['id', 'name']})
    return Response({'result': states, 'status_code': status.HTTP_200_OK})


@api_view(['GET'])
@jwt_required()
def city_list(request):
    state_id = request.data.get("state_id")
    cities = DbConn().get('res.city', 'search_read', [[['state_id', '=', int(state_id)]]],
                          {'fields': ['id', 'name']})
    return Response({'result': cities, 'status_code': status.HTTP_200_OK})


@api_view(['GET'])
@jwt_required()
def grn_list(request):
    create_uid = request.data.get("create_uid")
    grn_details = DbConn().get('syn.grn', 'search_read', [[['create_uid', '=', int(create_uid)]]],
                               {'fields': ['name', 'company_id', 'vendor_id', 'site_id', 'purchase_order_id']})

    for i in grn_details:
        i["grn_id"] = i.pop("id")
    return Response({'result': grn_details, 'status_code': status.HTTP_200_OK})


@api_view(['GET'])
@jwt_required()
def purchase_order_list(request):
    create_uid = request.data.get('create_uid')
    po_details = DbConn().get('syn.purchase.order', 'search_read', [[['create_uid', '=', int(create_uid)]]], {
        'fields': ['name', 'company_id', 'site_id', 'vendor_id', 'material_requisition_id', 'payment_terms_id',
                   'status']})
    for i in po_details:
        i["po_id"] = i.pop("id")
    return Response({'result': po_details, 'status_code': status.HTTP_200_OK})


@api_view(['GET'])
@jwt_required()
def view_grn(request):
    grn_id = request.data.get("grn_id")
    grn_details = DbConn().get('syn.grn', 'read', [[int(grn_id)]],
                               {'fields': ['name', 'company_id', 'vendor_id', 'site_id', 'purchase_order_id']})
    grn_line_details = DbConn().get('syn.grn.line', 'search_read', [[["grn_id", "=", int(grn_id)]]],
                                    {'fields': ['material_id', 'qty_received']})
    for i in grn_details:
        i["grn_id"] = i.pop("id")
    for j in grn_line_details:
        j["grn_line_id"] = j.pop("id")
    grn_details.append(grn_line_details)
    return Response(
        {'result': grn_details, 'status_code': status.HTTP_200_OK})


@api_view(['GET'])
@jwt_required()
def view_purchase_order(request):
    po_id = request.data.get("po_id")
    po_details = DbConn().get('syn.purchase.order', 'read', [[int(po_id)]], {
        'fields': ['name', 'company_id', 'site_id', 'vendor_id', 'material_requisition_id', 'payment_terms_id',
                   'status']})
    po_line_details = DbConn().get('syn.purchase.order.line', 'search_read', [[["purchase_order_id", "=", int(po_id)]]],
                                   {'fields': ['material_id', 'quantity']})
    for i in po_details:
        i["po_id"] = i.pop("id")
    for j in po_line_details:
        j["po_line_id"] = j.pop("id")
    po_details.append(po_line_details)
    return Response(
        {'result': po_details, 'status_code': status.HTTP_200_OK})
