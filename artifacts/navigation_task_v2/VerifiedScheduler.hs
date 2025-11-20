module VerifiedScheduler (
  Task(..),
  taskSet,
  schedule,
  deadlineMet,
  utilizationSafe,
  allTasksSafe
) where

import Data.List (foldl')

type Milliseconds = Int

data Task = Task
  { taskName :: String
  , period   :: Milliseconds
  , execution :: Milliseconds
  , deadline :: Milliseconds
  , priority :: Int
  } deriving (Eq, Show)

thigh, tmedium, tlow, tbackup, tdiag :: Task
thigh   = Task "T_High"        30   8   30   1
tmedium = Task "T_Medium"     100  30  100  2
tlow    = Task "T_Low"        150  20  150  3
tbackup = Task "T_Backup"     400  8   400  4
tdiag   = Task "T_Diagnostic" 800  10  800  5

taskSet :: [Task]
taskSet = [thigh, tmedium, tlow, tbackup, tdiag]

type Time = Int

schedule :: Task -> Time -> Bool
schedule Task{period = p, execution = c} t =
  let slot = t `mod` p
  in slot < c

deadlineMet :: Task -> Bool
deadlineMet Task{execution = c, deadline = d, period = p} = c <= d && d <= p

utilizationSafe :: Bool
utilizationSafe = totalUtil <= bound
  where
    n = fromIntegral (length taskSet)
    totalUtil = sum [fromIntegral (execution task) / fromIntegral (period task) | task <- taskSet]
    bound = n * ((2 ** (1 / n)) - 1)

allTasksSafe :: Bool
allTasksSafe = all deadlineMet taskSet && utilizationSafe
