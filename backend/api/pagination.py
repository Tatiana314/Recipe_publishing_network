"""
Настройка постраничной навигации.
"""
from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'
    page_query_param = 'page'
    max_page_size = 100
