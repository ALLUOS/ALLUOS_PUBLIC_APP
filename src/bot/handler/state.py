from telegram.ext import ConversationHandler

END = ConversationHandler.END

# states for the private base handler (min: 1, max: 99)
WFI_USER_NAME, WFD_FLASHBACK, WFD_CREATE_OR_JOIN_GROUP_OR_SEE_ACHIEVEMENTS, WFI_REGISTRATION_CODE, WFD_CODE_OR_CANCEL, WFD_SET_USER_NAME, WFD_PRIVACY_SETTINGS = range(
    1, 8)
# states for room handler and path handler
WAIT_FOR_USERS_TO_BE_READY, WAIT_FOR_TASK_SELECTION, WAIT_FOR_PASSCODE, WAIT_FOR_RESTART_POLL, WAIT_FOR_PATH_SEL = range(
    100, 105)
# states for Task 01 - sentence correction (min: 200, max: 299)
SEN_CORR_WAIT_FOR_ANSWER_SENTENCE, SEN_CORR_WAIT_FOR_ANSWER_IDENTIFICATION, SEN_CORR_WAIT_FOR_ANSWER_CORRECTION, SEN_CORR_END_SUCCESS, SEN_CORR_END_FAIL, SEN_CORR_SEL_WRONG_USER, SEN_CORR_STOP = range(
    200, 207)
# states for Task 02 - vocab description (min: 300, max: 399)
VOCAB_DESC_WAIT_FOR_GUESS, VOCAB_DESC_END_SUCCESS, VOCAB_DESC_END_FAIL, VOCAB_DESC_SEL_WRONG_USER, VOCAB_DESC_STOP = range(
    300, 305)
# states for Task 03 - discussion (min: 400, max: 499)
DISCUSS_Q1, DISCUSS_Q2, DISCUSS_Q3, DISCUSS_END_SUCCESS, DISCUSS_END_FAIL, DISCUSS_SEL_WRONG_USER, DISCUSS_STOP = range(
    400, 407)
# states for Task 04 - listening (min: 500, max:599)
DISCUSS, WAIT_FOR_ANSWER, CONFIRMATION, LISTENING_SEL_WRONG_USER, LISTENING_STOP, LISTENING_STOP, DISCUSSION_TIME = range(
    500, 507)
# states for auxiliary conversation handlers (FAQ and Tutorial)
FAQ_WAIT_FOR_POLL, TUTORIAL_WAIT_FOR_POLL = range(
    601, 603)

# Define here the identifiers for the user context data
USERS_NAME = 'users_name'
