class Pagination:
    def __init__(self, page=1, per_page=10):
        self.page = page
        self.per_page = per_page
        self.total = 0
    
    @property
    def offset(self):
        return (self.page - 1) * self.per_page
    
    @property
    def total_pages(self):
        return (self.total + self.per_page - 1) // self.per_page
    
    @property
    def has_prev(self):
        return self.page > 1
    
    @property
    def has_next(self):
        return self.page < self.total_pages
    
    def get_page_info(self):
        return {
            'current_page': self.page,
            'total_pages': self.total_pages,
            'per_page': self.per_page,
            'total_items': self.total,
            'has_prev': self.has_prev,
            'has_next': self.has_next
        }