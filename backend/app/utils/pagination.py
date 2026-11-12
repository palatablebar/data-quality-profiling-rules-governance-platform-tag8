"""Small offset/limit helper shared by list endpoints."""
MAX_PAGE_SIZE = 200


def paginate(items, page: int = 1, page_size: int = 50) -> dict:
    page = max(1, int(page or 1))
    page_size = max(1, min(MAX_PAGE_SIZE, int(page_size or 50)))
    total = len(items)
    start = (page - 1) * page_size
    return {
        "items": items[start:start + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


def paginate_query(query, page: int = 1, page_size: int = 50) -> dict:
    page = max(1, int(page or 1))
    page_size = max(1, min(MAX_PAGE_SIZE, int(page_size or 50)))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }
