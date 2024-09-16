from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import Organization, Employee, OrganizationResponsible, OrganizationType
from .database import AsyncSessionLocal
from uuid import uuid4


async def create_base_data():
    async with AsyncSessionLocal() as session:
        # Создание базовых данных
        await create_organization_and_user(session)
        await session.commit()


async def create_organization_and_user(session: AsyncSession):
    # Проверка существования данных в таблице Organization
    result = await session.execute(select(Organization).filter_by(name="Organization 1"))
    organization = result.scalars().first()

    if not organization:
        # Создание организации
        organization_id = uuid4()
        organization = Organization(
            id=organization_id,
            name="Organization 1",
            description="Test organization",
            type=OrganizationType.LLC.value,  # Использование строкового представления Enum
        )
        session.add(organization)

        # Создание пользователя
        user_id = uuid4()
        user = Employee(
            id=user_id,
            username="user1",
            first_name="John",
            last_name="Doe"
        )
        session.add(user)

        # Создание связки пользователя с организацией
        organization_responsible = OrganizationResponsible(
            id=uuid4(),
            organization_id=organization_id,
            user_id=user_id
        )
        session.add(organization_responsible)

        print("Base data created: Organization 1 and user1.")
    else:
        print("Base data already exists.")
