# Этот код разработан для СПО ПАК-П
# Место разработки: Военно-космическая академия имени А.Ф.Можайского
# Год разработки:2019
# Разработчик: Менисов А.Б.
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pakp.settings')

application = get_wsgi_application()
# Этот код разработан для СПО ПАК-П
# Место разработки: Военно-космическая академия имени А.Ф.Можайского
# Год разработки:2019
# Разработчик: Менисов А.Б.