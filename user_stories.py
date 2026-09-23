"""Central source of truth for EaglePark CSC 4610 user stories."""

USER_STORIES = [
    {
        "id": 'US-01',
        "board_number": 1,
        "github_issue": 16,
        "epic": 'Predictive Lot Occupancy & Forecasting',
        "story": 'As a ride commuting student, I want to have predictive parking capacity, so that I know which lots to avoid.',
    },
    {
        "id": 'US-02',
        "board_number": 2,
        "github_issue": 17,
        "epic": 'Predictive Lot Occupancy & Forecasting',
        "story": 'As a commuter student, I want to receive a push notification when my preferred lot is projected to fill up before my morning class, so that I can leave home earlier or select a backup lot.',
    },
    {
        "id": 'US-03',
        "board_number": 3,
        "github_issue": 18,
        "epic": 'Predictive Lot Occupancy & Forecasting',
        "story": 'As a commuter student, I want to view predicted parking lot fullness 20 minutes ahead of my arrival, so that I can drive straight to a lot with open stalls without circling.',
    },
    {
        "id": 'US-04',
        "board_number": 4,
        "github_issue": 19,
        "epic": 'Predictive Lot Occupancy & Forecasting',
        "story": 'As a university event coordinator, I want to forecast parking demand based on scheduled campus events, so that I can reserve specific lots in advance without displacing regular commuters.',
    },
    {
        "id": 'US-05',
        "board_number": 5,
        "github_issue": 20,
        "epic": 'Predictive Lot Occupancy & Forecasting',
        "story": 'As a campus visitor, I want to see real-time availability for designated visitor spaces, so that I do not park illegally in reserved permit zones.',
    },
    {
        "id": 'US-06',
        "board_number": 6,
        "github_issue": 21,
        "epic": 'Intelligent Routing & Dynamic Navigation',
        "story": 'As a commuter student, I want to input my class schedule and arrival time, so that the AI can recommend the optimal parking lot closest to my building.',
    },
    {
        "id": 'US-07',
        "board_number": 7,
        "github_issue": 22,
        "epic": 'Intelligent Routing & Dynamic Navigation',
        "story": 'As a commuter driver, I want real-time turn-by-turn navigation that routes me around campus choke points, so that I reach an available space in the least amount of transit time.',
    },
    {
        "id": 'US-08',
        "board_number": 8,
        "github_issue": 23,
        "epic": 'Intelligent Routing & Dynamic Navigation',
        "story": 'As a commuter driver, I want real-time navigation updates if my routed parking space gets taken by another driver, so that I will not arrive at a taken parking space.',
    },
    {
        "id": 'US-09',
        "board_number": 9,
        "github_issue": 24,
        "epic": 'Intelligent Routing & Dynamic Navigation',
        "story": 'As an electric vehicle owner, I want the map to prioritize routes to parking areas with available EV charging stalls, so that I can charge my car during class.',
    },
    {
        "id": 'US-10',
        "board_number": 10,
        "github_issue": 25,
        "epic": 'Intelligent Routing & Dynamic Navigation',
        "story": 'As a faculty member, I want to filter navigation destinations strictly by faculty/staff permit zones, so that I am guided only to lots where my permit is valid.',
    },
    {
        "id": 'US-11',
        "board_number": 11,
        "github_issue": 7,
        "epic": 'Administrative Privileges & Law Enforcement',
        "story": 'As a campus police officer, I want an audit log of reported rideshare safety incidents and driver identities, so that I can investigate policy violations or criminal activity.',
    },
    {
        "id": 'US-12',
        "board_number": 12,
        "github_issue": 9,
        "epic": 'Administrative Privileges & Law Enforcement',
        "story": 'As an IT specialist for TnTech, I want to enter the backend of the system, so that I can help upkeep the system.',
    },
    {
        "id": 'US-13',
        "board_number": 13,
        "github_issue": 10,
        "epic": 'Administrative Privileges & Law Enforcement',
        "story": "As law enforcement, I want to check a vehicle's history of parking so that I can determine the severity of their penalty.",
    },
    {
        "id": 'US-14',
        "board_number": 14,
        "github_issue": 13,
        "epic": 'Administrative Privileges & Law Enforcement',
        "story": 'As a parking enforcement officer, I want an administrative dashboard displaying lots that exceed permitted capacity, so that I can dispatch patrols efficiently.',
    },
    {
        "id": 'US-15',
        "board_number": 15,
        "github_issue": 14,
        "epic": 'Administrative Privileges & Law Enforcement',
        "story": 'As a facilities administrator, I want to view historical peak-hour occupancy reports across all campus zones, so that the university can make data-driven decisions about future parking expansions.',
    },
    {
        "id": 'US-16',
        "board_number": 16,
        "github_issue": 6,
        "epic": 'Smart Carpooling & Commuter Coordination / RideSharing',
        "story": 'As a commuter, I want to register my vehicle as a rideshare option so that I present myself as a legitimate driver available for others to join.',
    },
    {
        "id": 'US-17',
        "board_number": 17,
        "github_issue": 8,
        "epic": 'Smart Carpooling & Commuter Coordination / RideSharing',
        "story": 'As a faculty member, I want to filter available rideshare options so that I can match myself only with other faculty.',
    },
    {
        "id": 'US-18',
        "board_number": 18,
        "github_issue": 11,
        "epic": 'Smart Carpooling & Commuter Coordination / RideSharing',
        "story": 'As a commuter student, I want the system to match me with nearby classmates heading to campus at similar times, so that we can carpool and reduce parking demand.',
    },
    {
        "id": 'US-19',
        "board_number": 19,
        "github_issue": 12,
        "epic": 'Smart Carpooling & Commuter Coordination / RideSharing',
        "story": 'As a carpool participant, I want to earn preferred parking access or permit discounts, so that I have a tangible incentive to share rides consistently.',
    },
    {
        "id": 'US-20',
        "board_number": 20,
        "github_issue": 15,
        "epic": 'Smart Carpooling & Commuter Coordination / RideSharing',
        "story": 'As a student driver offering rides, I want to verify passenger pickup locations along my route, so that I do not add significant detour time to my morning commute.',
    },
]

FEATURE_STORY_MAP = {
    "Dashboard": ["US-01", "US-03", "US-05"],
    "Predictive Parking": ["US-01", "US-02", "US-03", "US-04", "US-05"],
    "Smart Route": ["US-06", "US-07", "US-08", "US-09", "US-10"],
    "RideShare": ["US-16", "US-17", "US-18", "US-19", "US-20"],
    "Admin & Evaluation": ["US-11", "US-12", "US-13", "US-14", "US-15"],
}

def get_story(story_id):
    return next((story for story in USER_STORIES if story["id"] == story_id), None)

def get_stories_for_feature(feature_name):
    ids = FEATURE_STORY_MAP.get(feature_name, [])
    return [story for story in USER_STORIES if story['id'] in ids]

def get_stories_for_epic(epic_name):
    return [story for story in USER_STORIES if story['epic'] == epic_name]