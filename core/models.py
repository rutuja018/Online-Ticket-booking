from django.db import models


class ContactInquiry(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact inquiry'
        verbose_name_plural = 'Contact inquiries'

    def __str__(self):
        return f"{self.name} <{self.email}>"
