from api.models import Course

for image1 in Image.objects.all():
    image1.image.name = image1.image.name.replace('old_path_prefix', 'new_path_prefix')
    image1.save()
    