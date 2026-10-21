from django.contrib import admin

# Register your models here.


from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "priority",
        "status",
        "created_by",
        "assigned_to",
        "created_at",
    )

    list_filter = ("category", "priority", "status")
    search_fields = ("title", "description", "created_by__username")
    readonly_fields = ("created_at", "updated_at")
