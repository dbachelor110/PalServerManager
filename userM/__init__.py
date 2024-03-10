from folders import SRC
import json
# 取得使用者資訊，若查無此使用者，回傳 fales
class UserInterFace:
    """
    A Inter Face for user
    -
    """
    def __init__(self,ID,NAME:str,PASSWORD:str,GROUP:str='guest') -> None:
        """
        A Inter Face for user
        -
        - id: Identify different user, unique
        - name: Disply name for user
        - password: Verify user login
        - group: Classify user so that you can design things like permissions"""
        self.ID=ID
        self.NAME:str=NAME
        self.PASSWORD:str=PASSWORD
        self.GROUP:str=GROUP
    
    def set(self,**kargs):
        """
        Set Variable
        -
        ID Cant Not Be setting, it will be ignore.
        
        args
        - NAME: Disply name for user
        - PASSWORD: Verify user login
        - GROUP: Classify user so that you can design things like permissions"""

        for key, value in kargs.items():
            if key in self.__dict__.keys():
                if key == 'ID': continue
                self.__dict__[key]=value
        self.save()
        
    def save(self):
        pass

    def __str__(self):
        out = f"""type: {self.__class__}\n"""
        out += f"name: {self.NAME}\n"
        out += f" id : {self.ID}\n"
        return out
    
    def __setattr__(self, name, value):
        if not name in self.__dict__:
            self.__dict__[name] = value

        elif name == 'ID':
            raise TypeError('User.ID is immutable')

    def __eq__(self, that):
        if not isinstance(that, UserInterFace):
            return False
        return self.ID == that.ID
        
    def __hash__(self):
        return self.ID

class User(UserInterFace):
    """
    User Class
    -
    Duplicate IDs are not allowed
    - USERS: A dict to cache users data and enshure id is unique."""
    
    USERS:dict[str,UserInterFace] = {}

    def __init__(self, ID, NAME: str, PASSWORD: str, GROUP: str = 'guest') -> None:
        if ID in User.USERS:
            self = User.USERS[ID]
        else:
            super().__init__(ID, NAME, PASSWORD, GROUP)
            User.USERS[ID] = self
            self.save()
    
    def save(self):
        """Save User to Data File"""
        try:
            with open(f'{SRC}/users.json','r',encoding='utf-8')as Data:
                usersData = Data.read()
        except:
            with open(f'{SRC}/users.json','w',encoding='utf-8')as Data:
                Data.write(json.dumps({}))
            usersData = '{}'

        with open(f'{SRC}/users.json','w',encoding='utf-8')as Data:
            users:dict = json.loads(usersData)
            users.update({self.ID:self.__dict__})
            Data.write(json.dumps(users))


    def get(id:str):
        """From USERS get a User.
        
        If not find the id in USERS, return None."""
        if id in User.USERS: return User.USERS[id]
        else: return None
    
    def load():
        """
        Load Users Data From File to Memory
        -
        """
        with open(f'{SRC}/users.json','w',encoding='utf-8')as Data:
            usersData = Data.read()
        if usersData:
            users = json.loads(usersData)
            for user in users.values():
                User(**user)

class PalUser(User):
    USERS:dict[str,UserInterFace]={}
    def __init__(self, id, name: str) -> None:
        password:str = ''
        group:str = 'pal'
        super().__init__(id, name, password, group)

User('admin','admin','admin','admin')


if __name__ == '__main__':
    print('make 5 user')
    for i in range(5):
        User(f'ID{i}',f'User{i}','passw')
    for user in User.USERS.values():
        print(user)

    print('try replase 5 user')
    for i in range(5):
        User(f'ID{i}',f'User{i+5}','passw')
    for user in User.USERS.values():
        print(user)
    
    print('try edit 5 user')
    for user in User.USERS.values():
        user.set(NAME = 'edit')
        print(user)
    
    print('try user eq')
    users = User.USERS
    print(users['ID0']==users['ID4'])
    