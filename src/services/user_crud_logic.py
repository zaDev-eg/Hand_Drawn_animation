
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user_model import UserModel
from ..schemas.request_schema import CreateUser, UpdateUser, UserRole
from ..utils.password_hashing import hashing_password, varifying_password


class UserService:

    async def get_user_by_id(
        self,
        user_id: UUID,
        session: AsyncSession,
    ) -> UserModel | None:

        result = await session.execute(
            select(UserModel).where(UserModel.user_id == user_id)
        )

        return result.scalars().first()


    async def get_user_by_email(
        self,
        email: str,
        session: AsyncSession,
    ) -> UserModel | None:

        result = await session.execute(
            select(UserModel).where(UserModel.email == email)
        )

        return result.scalars().first()


    async def get_all_users(
        self,
        session: AsyncSession,
    ) -> list[UserModel]:

        result = await session.execute(
            select(UserModel).order_by(UserModel.created_at.desc())
        )

        return list(result.scalars().all())


    async def authenticate(
        self,
        email: str,
        password: str,
        session: AsyncSession,
    ) -> UserModel | None:

        user = await self.get_user_by_email(email, session)

        if user is None:
            return None

        if not varifying_password(password, user.hashed_password):
            return None

        return user


    async def create_user(
        self,
        user_data: CreateUser,
        session: AsyncSession,
    ) -> UserModel | None:

        existing_user = await self.get_user_by_email(
            str(user_data.email),
            session,
        )

        if existing_user:
            return None

        user = UserModel(
            username=user_data.username,
            email=str(user_data.email),
            hashed_password=hashing_password(user_data.password),
            role=UserRole.USER.value,
            is_verified=False,
        )

        session.add(user)

        try:
            await session.commit()

        except IntegrityError:
            await session.rollback()
            return None

        await session.refresh(user)

        return user


    async def update_user(
        self,
        user: UserModel,
        user_data: UpdateUser,
        session: AsyncSession,
    ) -> UserModel:

        updates = user_data.model_dump(exclude_unset=True)

        new_password = updates.pop("password", None)
        new_email = updates.pop("email", None)

        for key, value in updates.items():
            setattr(user, key, value)

        if new_password is not None:
            user.hashed_password = hashing_password(new_password)

        if new_email is not None and str(new_email) != user.email:

            user.email = str(new_email)
            user.is_verified = False

        user.updated_at = datetime.now(timezone.utc)

        session.add(user)

        await session.commit()
        await session.refresh(user)

        return user


    async def update_role(
        self,
        user: UserModel,
        role: UserRole,
        session: AsyncSession,
    ) -> UserModel:

        user.role = role.value
        user.updated_at = datetime.now(timezone.utc)

        session.add(user)

        await session.commit()
        await session.refresh(user)

        return user


    async def delete_user(
        self,
        user: UserModel,
        session: AsyncSession,
    ) -> None:

        await session.delete(user)
        await session.commit()


    async def set_user_password(
        self,
        user: UserModel,
        new_password: str,
        session: AsyncSession,
    ) -> None:

        user.hashed_password = hashing_password(new_password)
        user.updated_at = datetime.now(timezone.utc)

        session.add(user)

        await session.commit()
        await session.refresh(user)


    async def verify_user_email(
        self,
        user: UserModel,
        session: AsyncSession,
    ) -> None:

        if not user.is_verified:

            user.is_verified = True
            user.updated_at = datetime.now(timezone.utc)

            session.add(user)

            await session.commit()
            await session.refresh(user)