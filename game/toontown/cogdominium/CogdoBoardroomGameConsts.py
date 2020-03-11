from direct.fsm.StatePush import StateVar
from game.otp.level.EntityStateVarSet import EntityStateVarSet
from game.toontown.cogdominium.CogdoEntityTypes import CogdoBoardroomGameSettings
Settings = EntityStateVarSet(CogdoBoardroomGameSettings)
GameDuration = StateVar(60.0)
FinishDuration = StateVar(10.0)
