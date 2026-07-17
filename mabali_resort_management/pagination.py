"""Generic pagination utilities for reuse across the project."""


class SimplePage:
    """Lightweight page object compatible with Django template pagination patterns."""

    def __init__(self, object_list, number, total_pages, total_count):
        self.object_list = list(object_list)
        self.number = number
        self.paginator = type(
            "P",
            (),
            {
                "num_pages": total_pages,
                "count": total_count,
                "page_range": range(1, total_pages + 1),
            },
        )()

    @property
    def has_previous(self):
        return self.number > 1

    @property
    def has_next(self):
        return self.number < self.paginator.num_pages

    def previous_page_number(self):
        return self.number - 1

    def next_page_number(self):
        return self.number + 1

    def start_index(self):
        if self.paginator.count == 0:
            return 0
        return (self.number - 1) * len(self.object_list) + 1

    def end_index(self):
        if self.paginator.count == 0:
            return 0
        return (self.number - 1) * len(self.object_list) + len(self.object_list)


def paginate_queryset(request, queryset, per_page=20, page_param="page"):
    """
    Generic pagination helper.

    Returns a dict with:
        - page_obj:      the current Page object (has .has_previous, .has_next, etc.)
        - items:         the items on the current page
        - page_range:    range object for rendering page numbers
        - current_page:  current page number (int)
        - total_pages:   total number of pages
        - total_count:   total number of items in the queryset

    Usage in a view::

        from mabali_resort_management.pagination import paginate_queryset

        def my_view(request):
            qs = MyModel.objects.all()
            ctx = paginate_queryset(request, qs, per_page=20)
            return render(request, 'my_template.html', ctx)

    Usage in a template::

        {% include "components/pagination.html" with page_obj=page_obj %}
    """
    total_count = queryset.count()
    total_pages = max(1, -(-total_count // per_page))  # ceil division

    raw_page = request.GET.get(page_param, 1)
    try:
        current_page = int(raw_page)
    except (TypeError, ValueError):
        current_page = 1
    current_page = max(1, min(current_page, total_pages))

    start = (current_page - 1) * per_page
    end = start + per_page
    items = list(queryset[start:end])

    page_obj = SimplePage(items, current_page, total_pages, total_count)

    return {
        "page_obj": page_obj,
        "items": page_obj.object_list,
        "page_range": page_obj.paginator.page_range,
        "current_page": page_obj.number,
        "total_pages": total_pages,
        "total_count": total_count,
    }
