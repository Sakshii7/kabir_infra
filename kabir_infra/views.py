import xmlrpc.client

from django_jwt_extended import create_access_token, create_refresh_token
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
    user_id = common.authenticate(db, user_name, user_pass, {})
    user_details = DbConn().get('res.users', 'read', [[int(user_id)]],
                                {'fields': ['name', 'partner_id']})[0]
    return Response({'user_details': {"user_id": user_details["id"], "user_name": user_details["name"],
                                      "partner_details  ": user_details["partner_id"],
                                      'tokens': {
                                          "access_token": create_access_token(
                                              identity={'user_details': user_details, 'username': user_name}),
                                          'refresh_token': create_refresh_token(
                                              identity={'user_details': user_details, 'username': user_name})},
                                      'status_code': status.HTTP_200_OK}})
