
## Imports 
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user_model import UserModel
from ..utils.password_hashing import hashing_password, varifying_password
from ..schemas.request_schema import CreateUser, UpdateUser



class UserService(): 
    def __init__(self, session: AsyncSession):
        self.session = session
        
        
        
    async def get_all_users(self): 
        ## build the statement 
        statement = select(UserModel).order_by(desc(UserModel.created_at))
        
        ## execute the statement 
        result = await self.session.execute(statement)
        ## fetch all results 
        users = result.scalars().all()
        
        ## simple check 
        if not users:
            return None
        else:
            return users
    
    async def get_user_by_email(self, email: str, password: str): 
        ## build the statement 
        statement = select(UserModel).where(UserModel.email == email)
        
        ## execute the statement 
        result = await self.session.execute(statement)
        
        ## fetch the results
        user = result.scalars().first()
    
        ## simple check 
        if user is None:
            return None
        
        ## check if the password is correct 
        check = varifying_password(password, user.hashed_password)
        
        ## check 
        if check: 
            return user
        else: 
            return None
    
    async def create_user(self, user_data: CreateUser): 
        ## simple check 
        user = await self.get_user_by_email(email=CreateUser.email, 
                                            password=CreateUser.password)
        
        ## check 
        if user is None: 
            ## dump the object info 
            new_user = user_data.model_dump()
            
            ## value mapping (unpack)
            new_user = UserModel(**new_user)
            
            ## hash the password 
            new_user.hashed_password = hashing_password(user_data.password)
            
            ## add the user in the db 
            self.session.add(new_user)
            
            ## save changes
            await self.session.commit()

            ## solution for MissingGreenLet problem
            await self.session.refresh(new_user)
            
            return new_user
            
    
    async def update_user(self, email: str, password: str, user_data: UpdateUser): 
        user = await self.get_user_by_email(email, password)

        ## check 
        if user is None: 
            return None 
        
        new_user = user_data.model_dump(exclude_unset=True)
        
        ## set the new updates
        for k, v in new_user.items():
            setattr(user, k, v)
    
        self.session.add(user)

        ## save updates
        await self.session.commit()

        return user
    
    async def delete_user(self, email: str, password: str): 
        user = await self.get_user_by_email(email, password)
        if user is None:
            return None

        await self.session.delete(user)
        await self.session.commit()
        
        return True  ## -> user was existed and deleted successfully 
    
    
    ## update the user email state to be verified
    async def verify_user_email(
        self,
        user: UserModel,
        updated_data: dict,
    ) -> None:
        ## add the new update to the user 
        for k, v in updated_data.items(): 
            setattr(user, k, v)
        
        ## save updates
        await self.session.commit()
        return None