import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy.future import select
from app.auth.models import User
from app.auth.jwt_handler import create_access_token
from datetime import timedelta
import urllib.request, json
import io

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        user = result.scalars().first()
        if not user:
            print("No users found")
            return
            
        access_token = create_access_token(
            data={"sub": user.email, "role": user.role}, 
            expires_delta=timedelta(minutes=60)
        )
        
        # We need to construct a multipart/form-data request
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="file"; filename="test.pdf"\r\n'
            f'Content-Type: application/pdf\r\n\r\n'
            f'dummy pdf content\r\n'
            f'--{boundary}--\r\n'
        ).encode('utf-8')
        
        req = urllib.request.Request(
            'http://localhost:8000/workspaces/17/documents', 
            data=body, 
            headers={
                'Content-Type': f'multipart/form-data; boundary={boundary}',
                'Authorization': f'Bearer {access_token}'
            }
        )
        try:
            res = urllib.request.urlopen(req)
            print(res.read().decode())
        except Exception as e:
            print(e)
            if hasattr(e, 'read'):
                print("BODY:", e.read().decode())

asyncio.run(main())
