from django.db import models


# Create your models here.


## A model for the various cohorts joining the program
class Cohort(models.Model):
    cohort_name = models.CharField(max_length=150)
    cohort_start = models.DateTimeField(auto_now_add=True)
    cohort_end = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.cohort_name
    

## A model for the student's attendance throughout the cohort in weekly breakdown
CHOICES = (
    ("absent", "absent"), 
    ("present", "present"),
)    
class WeeklyAttendance(models.Model):
    week = models.CharField(max_length=150)
    student_attendance = models.Choices(choices = CHOICES)




## The structure for the student, with the key details intended to be captured. 
class Student(models.Model):
    name = models.CharField(max_length=150)
    email = models.CharField(max_length=150)
    cohort = models.ForeignKey(Cohort, related_name='current-cohort', on_delete=models.CASCADE)
    ranking = models.PositiveIntegerField()
    assignment_completion = models.PositiveIntegerField()
    attendance_average = models.DecimalField(max_digits= 4, decimal_places= 2, default= 0.0)




