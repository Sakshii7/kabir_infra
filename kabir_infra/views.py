import xmlrpc.client

from django_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from kabir_infra_app.db_conn import DbConn
from utilis import Environment, Models

url = Environment.get("HOST_URL")
db = Environment.get("DATABASE_NAME")
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))


@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    try:
        user_id = common.authenticate(db, username, password, {})
        user_details = DbConn().get(Models.user, 'read', [[int(user_id)]],
                                    {'fields': ['name', 'partner_id', 'login']})
        for user in user_details:
            user["user_id"] = user.pop("id")
            user["email"] = user.pop("login")

        return Response(
            {'result': user_details, 'tokens': {
                "access_token": create_access_token(identity={'user_details': user_details, 'username': username}),
                'refresh_token': create_refresh_token(identity={'user_details': user_details, 'username': username})},
             'status_code': status.HTTP_200_OK})

    except Exception:
        return Response({"result": "Invalid Username or Password", "status_code": status.HTTP_400_BAD_REQUEST},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@jwt_required()
def my_profile(request):
    identity = get_jwt_identity(request)
    partner_id = identity["user_details"][0]["partner_id"][0]
    user_profile = DbConn().get(Models.user, 'search_read', [[['partner_id', '=', int(partner_id)]]],
                                {'fields': ['name', 'father_name', 'code', 'mobile', 'email']})
    for user in user_profile:
        user["user_id"] = user.pop("id")
    return Response({'result': user_profile, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


@api_view(['GET'])
@jwt_required()
def get_country_list(request):
    countries = DbConn().get(Models.country, 'search_read', [[]], {'fields': ['id', 'name']})
    return Response({'result': countries, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


@api_view(['GET'])
@jwt_required()
def get_state_list(request):
    country_id = request.query_params.get("country_id")
    states = DbConn().get(Models.state, 'search_read', [[['country_id', '=', int(country_id)]]],
                          {'fields': ['id', 'name']})
    return Response({'result': states, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


@api_view(['GET'])
@jwt_required()
def get_city_list(request):
    state_id = request.query_params.get("state_id")
    cities = DbConn().get(Models.city, 'search_read', [[['state_id', '=', int(state_id)]]],
                          {'fields': ['id', 'name']})
    return Response({'result': cities, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


@api_view(['GET'])
@jwt_required()
def get_site_list(request):
    sites = DbConn().get(Models.site, 'search_read', [[['status', '=', 'inprogress']]], {'fields': ['id', 'name']})
    return Response({'result': sites, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


@api_view(['GET'])
@jwt_required()
def get_vendor_list(request):
    vendors = DbConn().get(Models.vendor, 'search_read', [[]], {'fields': ['id', 'name']})
    return Response({'result': vendors, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


@api_view(['GET'])
@jwt_required()
def get_grn_list(request):
    site_id = request.query_params.get("site_id")
    identity = get_jwt_identity(request)
    user_id = identity["user_details"][0]["user_id"]
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    search_domain = [['create_uid', '=', int(user_id)], ['site_id', '=', int(site_id)]]
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
                            {'fields': ['name', 'vendor_id', 'site_id', 'grn_date']})
    for grn in grn_list:
        grn["grn_id"] = grn.pop("id")
    return Response({'result': grn_list, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


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
    return Response(
        {'result': grn_details, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


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
    return Response({'result': purchase_order_list}, status=status.HTTP_200_OK)


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
                                          {'fields': ['name', 'company_id', 'site_id', 'vendor_id', 'order_date',
                                                      'status']})
    for purchase_order in purchase_order_details:
        purchase_order["purchase_order_id"] = purchase_order.pop("id")
    return Response({'result': purchase_order_details, 'status_code': status.HTTP_200_OK},
                    status=status.HTTP_200_OK)


@api_view(['GET'])
@jwt_required()
def view_purchase_order(request):
    purchase_order_id = request.query_params.get("purchase_order_id")
    purchase_order_details = DbConn().get(Models.purchase_order, 'read',
                                          [[int(purchase_order_id)]], {
                                              'fields': ['name', 'company_id', 'site_id', 'vendor_id',
                                                         'material_requisition_id', 'status']})
    purchase_order_lines = DbConn().get(Models.purchase_order_line, 'search_read',
                                        [[["purchase_order_id", "=", int(purchase_order_id)]]],
                                        {'fields': ['material_id', 'quantity', 'qty_received', 'uom_id']})
    for line in purchase_order_lines:
        line["purchase_order_line_id"] = line.pop("id")
        material_id = line["material_id"][0]
        materials = DbConn().get('syn.material', 'read', [[material_id]], {'fields': ['allowable_tolerance']})
        allowable_tolerance = materials[0]['allowable_tolerance']
        calculation = line["quantity"] * allowable_tolerance / 100 + line["quantity"] - line["qty_received"]
        line["balance_qty"] = round(calculation)

    for purchase_order in purchase_order_details:
        purchase_order["purchase_order_id"] = purchase_order.pop("id")
        purchase_order['status'] = str(purchase_order["status"]).capitalize()
        purchase_order['purchase_order_lines'] = purchase_order_lines
    return Response(
        {'result': purchase_order_details, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


@api_view(['GET'])
@jwt_required()
def get_material_requisition_list(request):
    site_id = request.query_params.get('site_id')
    identity = get_jwt_identity(request)
    user_id = identity["user_details"][0]["user_id"]
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    domain = [['site_id', '=', int(site_id)], ['user_id', '=', int(user_id)]]
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
                                             {'fields': ['name', 'site_id', 'requisition_date']})
    for material_requisition in material_requisition_list:
        material_requisition['material_requisition_id'] = material_requisition.pop("id")
    return Response({'result': material_requisition_list, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


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

    for mat in material_requisition_lines:
        mat['line_id'] = mat.pop("id")
        material_id = mat["material_id"][0]
        po_list = []
        for po in purchase_order_list:
            po_id = po["id"]
            purchase_order_lines = DbConn().get(Models.purchase_order_line, 'search_read',
                                                [[["purchase_order_id", "=", po_id],
                                                  ['material_id', '=', material_id]]],
                                                {'fields': ['material_id', 'purchase_order_id']})
            if purchase_order_lines:
                po_list.append(po)
        mat['po_list'] = po_list
    for purchase_order in purchase_order_list:
        purchase_order['purchase_order_id'] = purchase_order.pop("id")
    for material_requisition in material_requisition_details:
        material_requisition['material_requisition_id'] = material_requisition.pop("id")
        material_requisition['rqn_lines'] = material_requisition_lines

    return Response({'result': material_requisition_details, 'status_code': status.HTTP_200_OK},
                    status=status.HTTP_200_OK)


@api_view(['POST'])
@jwt_required()
def add_material_requisition(request):
    site_id = request.data.get('site_id')
    materials = request.data.get('materials')
    material_data = eval(materials.replace('\\', ''))
    material_requisition_id = DbConn().get(Models.material_requisition, 'create', [{'site_id': int(site_id)}])
    for mat in material_data:
        mat['material_requisition_id'] = material_requisition_id
        DbConn().get(Models.material_requisition_line, 'create', [mat])
    material_requisition_details = DbConn().get(Models.material_requisition, 'read', [[material_requisition_id]],
                                                {'fields': ['name', 'site_id', 'requisition_date']})

    for material_requisition in material_requisition_details:
        material_requisition["material_requisition_id"] = material_requisition.pop("id")
        material_requisition['material_requisition_lines'] = material_data
    return Response({'result': material_requisition_details, 'status_code': status.HTTP_200_OK},
                    status=status.HTTP_200_OK)


@api_view(['GET'])
@jwt_required()
def get_company_list(request):
    companies = DbConn().get(Models.company, 'search_read', [[]],
                             {'fields': ['id', 'name', 'partner_id', 'mobile', 'email']})
    return Response({'result': companies, 'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)


@api_view(['GET'])
@jwt_required()
def management_dashboard(request):
    company_id = request.query_params.get('company_id')
    active_sites = DbConn().get(Models.site, 'search_read',
                                [[['company_id', '=', int(company_id)], ['status', '=', 'inprogress']]],
                                {'fields': ['name', 'shape_paths', 'shape_type']})
    total_outstanding = 0.0
    no_of_sites = len(active_sites)
    for site in active_sites:
        site_id = site["id"]
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
        {'result': {'sites': active_sites, 'total_outstanding': total_outstanding, 'no_of_sites': no_of_sites},
         'status_code': status.HTTP_200_OK}, status=status.HTTP_200_OK)
