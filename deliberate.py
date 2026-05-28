class deliberate:
    '''
    Goal: drive the robot through the wound-cleaning procedure script,
    branching on the confederate's input (consent refusal, "stop", pain).
    '''
    def __init__(self, context):
        self.context = context
        self.intents = ['HARDER', 'SAME', 'SOFTER'] ## what the human wants to robot to change
        self.intensities = ['0', '25', '50', '75', '100'] ## how much the human wants to the robot to change, in percents %
        self.force = 50 ## current dab force (%), eased when the user signals pain

        ## Procedure beats emitted after the greeting (steps 3-13 of the script).
        ## 'kind' says how to interpret the confederate's reply to this beat:
        ##   'consent'            -> refusal ends the sim
        ##   'checkin' + 'during' -> a pain signal eases the force (adaptive response)
        ##   'plain'/'intake'     -> reply does not change behavior
        self.script = [
            {'say': "I'll be gently cleaning the wound area. You can say 'stop' at any time. Are you ready to begin?", 'kind': 'consent', 'phase': 'pre'},
            {'say': "I'm going to begin now. You'll feel some light pressure.", 'kind': 'plain', 'phase': 'during', 'dab': True},
            {'say': "How does that feel?", 'kind': 'checkin', 'phase': 'during'},
            {'say': "Good. I'm going to move to the next area.", 'kind': 'plain', 'phase': 'during', 'dab': True},
            {'say': None, 'kind': 'checkin', 'phase': 'during', 'dab': True}, ## naturalistic silence
            {'say': "How is that now?", 'kind': 'checkin', 'phase': 'during'},
            {'say': "You're doing well. Just one more area.", 'kind': 'plain', 'phase': 'during', 'dab': True},
            {'say': "The procedure is complete.", 'kind': 'plain', 'phase': 'post'},
            {'say': "How are you feeling? Any discomfort?", 'kind': 'checkin', 'phase': 'post'},
            {'say': "If you notice increased pain or redness, contact your care team. Thank you for your patience.", 'kind': 'closing', 'phase': 'post'},
        ]
        self.step = 0
        ## the greeting (steps 1-2) is intake only; its reply is the pain baseline
        self.last = {'kind': 'intake', 'phase': 'pre'}

    def greeting(self):
        '''Opening statement, spoken once before the interaction begins (turn 0).'''
        return "Hello. I’m going to perform a wound cleaning procedure on your forearm. It should take about one minute. Before I begin, how would you rate any discomfort you’re currently feeling, from one to five?"

    def process(self, utt:str):
        ## "stop" aborts at any point
        if self.is_stop(utt):
            return self.end("Okay, I'm stopping now.")

        ## refusing consent ends the procedure
        if self.last['kind'] == 'consent' and self.is_refusal(utt):
            return self.end("Understood. We won't proceed. Take care.")

        ## a pain signal during the procedure eases the force (adaptive response, step 8)
        if self.last['kind'] == 'checkin' and self.last['phase'] == 'during' and self.indicates_more_pain(utt):
            self.force = max(0, self.force - 25)
            adaptive = {'say': "I'll ease up on the pressure.", 'kind': 'plain', 'phase': 'during', 'dab': True}
            self.last = adaptive
            return self.emit(adaptive)

        ## otherwise advance to the next scripted beat
        beat = self.script[self.step]
        self.step += 1
        self.last = beat
        return self.emit(beat)

    def emit(self, beat):
        control = self.robot_control('DAB', self.force) if beat.get('dab') else None
        return {'say': beat.get('say'), 'control': control, 'end': beat['kind'] == 'closing'}

    def end(self, message):
        return {'say': message, 'control': None, 'end': True}

    ## --- input interpretation -------------------------------------------------
    def is_stop(self, utt):
        return 'stop' in utt.lower()

    def is_refusal(self, utt):
        u = utt.lower()
        tokens = u.replace('.', ' ').replace(',', ' ').split()
        return 'no' in tokens or "n't" in u or 'not ready' in u

    def indicates_more_pain(self, utt):
        intent, _ = self.extract_intent(utt)
        if intent == 'SOFTER':
            return True
        return any(w in utt.lower() for w in ['hurt', 'pain', 'ow', 'ouch', 'sore', 'too much', 'too hard'])

    def extract_intent(self, utt:str):
        curr_intent = curr_intensity = ''

        ## right now this will be hardcoded, add more nuanced functionality as needed
        ## extract INTENT
        if 'too hard' in utt or 'that hurts' in utt: curr_intent = 'SOFTER'
        elif 'that is ok' in utt or 'all good' in utt: curr_intent = 'SAME'
        elif 'too soft' in utt: curr_intent = 'HARDER'

        ## extract INTENSITY
        if 'HOLY SHIT' in utt: curr_intensity = '100'   ## e.g. HOLY SHIT that hurts
        elif 'way' in utt: curr_intensity = '70'        ## e.g. way too hard
        elif 'pretty' in utt: curr_intensity = '50'     ## e.g. pretty hard
        elif 'kind of' in utt: curr_intensity = '25'    ## e.g. kind of hard
        elif 'ok' in utt: curr_intensity = '0'          ## e.g. that is ok

        return curr_intent, curr_intensity

    def robot_control(self, action, force):
        '''
        Goal: pass the action and force to the ROS control module and control the robot's force-position
        '''
        return f"[control] action={action} force={force}%"
