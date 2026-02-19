from django.contrib import admin

# Register your models here.

# Register your models here.
from .models import *
from .models import ChatMessage


admin.site.register(Item)
admin.site.register(ItemImage)
admin.site.register(UserProfile)
admin.site.register(Department)
admin.site.register(Contact)
admin.site.register(Announcement)
admin.site.register(Category)
admin.site.register(Career)
admin.site.register(JobApplication)
admin.site.register(SoftwareRequest)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(StudentProgress)
admin.site.register(Material)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Assignment)
admin.site.register(Exam)
admin.site.register(Submission)
admin.site.register(Grade)
admin.site.register(Cyber_Service)
admin.site.register(Cyber_Order)
admin.site.register(Robot)
admin.site.register(LoanRecipient)
@admin.register(ChatMessage)

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "user_message", "bot_reply", "created_at")
    search_fields = ("user_message", "bot_reply")
    list_filter = ("created_at",)


admin.site.site_header = "Bentha Technologies"
admin.site.site_title = "Bentha Technologies Administration"
admin.site.index_title = "Welcome To Your Bentha Technologies Management Platform"