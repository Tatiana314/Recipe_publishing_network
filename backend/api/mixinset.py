from rest_framework import status
from rest_framework.response import Response


class DeleteObjectMixin:
    """Удаление объекта."""

    def delete_obj(self, obj):
        if obj:
            obj.delete()
            return Response(
                'Объект удален.', status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'errors': 'Объект не существует.'},
            status=status.HTTP_400_BAD_REQUEST
        )
