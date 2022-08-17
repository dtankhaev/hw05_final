from django.conf import settings
from django.core.paginator import Paginator


def new_paginator(obj_list, page):
    paginator = Paginator(obj_list, settings.NUMBER_OF_PAGINATOR)
    page_obj = paginator.get_page(page)
    return page_obj
