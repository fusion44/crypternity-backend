from django.db import models


class Project(models.Model):
    id = models.AutoField(primary_key=True)
    creator = models.ForeignKey(
        'auth.user',
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
