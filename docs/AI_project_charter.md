# CSC 4610 Software Engineering: AI Lab #3 - Project Charter and Stakeholder Matrix

---

## 1. Project Charter

### Project Title
Smart Campus Parking and Rideshare Optimization Platform (`smart-campus-parking-ai`)

### Executive Summary and Problem Statement
Campus parking congestion creates predictable delays, wasted fuel, and class tardiness for students and faculty. Constructing new physical parking facilities requires millions of dollars in capital expenditure and takes away scarce campus land. 

This project delivers an AI-driven transit and navigation system that optimizes existing infrastructure. By combining real-time edge computer vision for parking occupancy tracking with density-based rideshare clustering, the platform directs drivers to open spaces before lots become saturated and pairs commuters into shared rides to lower overall campus vehicle volume.

### Project Goals and Business Objectives
* **Reduce Parking Search Time:** Lower average morning search times from 15 to 20 minutes down to under 5 minutes during peak campus arrival windows.
* **Cut Single-Occupancy Vehicles:** Decrease single-occupancy student vehicles driving to campus by 15% through timetable-synchronized carpool matching.
* **Proactive Load Balancing:** Automatically divert inbound drivers away from lots reaching 90% saturation to peripheral overflow lots before entrance queues form.
* **Cost-Effective Implementation:** Leverage existing campus security camera feeds and edge processing devices rather than purchasing expensive per-space in-ground sensors.

### Scope Definition
* **In-Scope:**
  * Ingestion and simulation of campus camera telemetry using edge computer vision models.
  * Spatial rideshare matchmaking using spherical Haversine DBSCAN based on student class schedules and home coordinates.
  * Driver navigation dashboard featuring real-time occupancy status and automated rerouting suggestions.
  * Privacy-preserving data architecture that clusters commuters without exposing raw street addresses.
* **Out-of-Scope:**
  * Physical gate arm hardware integration or automated citation enforcement.
  * In-app financial payment processing or money transfers between students.
  * City-wide municipal transit routing beyond university perimeter corridors.

### Project Constraints and Assumptions
* **Constraints:**
  * Real-time lot occupancy status must update across the system every 10 seconds or faster.
  * Inference and API operating costs must remain below $0.05 per active user session.
  * Strict compliance with FERPA regulations regarding student location and class schedule privacy.
* **Assumptions:**
  * Existing campus security cameras offer sufficient field-of-view coverage over primary commuter surface lots.
  * Students are willing to share rides if detour pickups remain under 1.5 kilometers of their primary route.

### Key Milestones and Deliverables
| Milestone | Key Deliverable | Status |
| :--- | :--- | :--- |
| **Iteration Zero** | Repository scaffolding, synthetic schedule data generator, baseline Streamlit and Pydeck map interface | Completed |
| **Sprint 1** | Dynamic 90% lot reroute triggers, interactive DBSCAN parameter controls, initial backlog tracking | Active |
| **Sprint 2** | Historical turnover forecasting models tied to class dismissal bells, camera weather degradation handling | Scheduled |
| **Pilot Evaluation** | Controlled pilot deployment across 2 to 3 high-traffic commuter parking facilities | Scheduled |

---

## 2. Stakeholder Identification and Analysis

| Stakeholder Group | Role in Project | Primary Interests and Expectations | Key Concerns |
| :--- | :--- | :--- | :--- |
| **Commuter Students** | Primary End Users (Drivers and Riders) | Fast parking spot discovery, lower fuel costs, and dependable rideshare pickups | Personal safety with unfamiliar peers, route delays, and mobile location privacy |
| **Faculty and Staff** | Secondary End Users and Beneficiaries | On-time arrival for lectures and meetings, reliable parking availability near department buildings | Spillover of student vehicles into reserved faculty and staff spaces |
| **Campus Police and Parking Services** | Operational Stakeholders | Smooth traffic flow, fewer roadway bottlenecks, reduced parking violations, and clear emergency access | Network bandwidth usage from camera feeds and potential university liability in carpools |
| **University Administration and IT** | Infrastructure and Compliance Gatekeepers | Low infrastructure cost, reliable software uptime, and strict data protection standards | Regulatory compliance (FERPA) and protection against unauthorized tracking of student movements |
| **Engineering Project Team** | Development and Delivery (Scrum Team) | Delivering working software iterations on schedule, maintaining algorithm precision, and writing clean code | Edge camera vision degradation from weather, user adoption hurdles, and tight academic deadlines |

---

## 3. Stakeholder Power and Interest Matrix

The matrix below maps project stakeholders according to their level of **Influence (Power)** over project decisions and their level of **Interest** in daily operations.

| | Low Interest | High Interest |
| :--- | :--- | :--- |
| **High Influence** | **Meet Their Needs**<br><br>• Campus Police & Parking Services | **Manage Closely (Key Players)**<br><br>• University Administration & IT<br>• Commuter Student Body |
| **Low Influence** | **Monitor (Minimum Effort)**<br><br>• Local Municipality & Surrounding Community | **Keep Informed**<br><br>• Faculty & University Staff |

---

## 4. Stakeholder Engagement Strategy

* **Manage Closely (High Power, High Interest):**
  * **Commuter Students:** Collect direct user feedback during sprint reviews, design clear user controls, and build transparent privacy settings into the mobile interface to support early adoption.
  * **University Administration and IT:** Conduct regular security reviews, verify FERPA compliance for timetable data, and demonstrate low network and server resource usage.
* **Meet Their Needs (High Power, Low Interest):**
  * **Campus Police and Parking Services:** Deliver automated administrative reports showing traffic reductions and ensure the system runs without requiring intervention or daily management from parking enforcement personnel.
* **Keep Informed (Low Power, High Interest):**
  * **Faculty and University Staff:** Provide regular milestone updates demonstrating improvements in peak morning arrival times and highlighting measures that safeguard faculty-designated parking zones.
* **Monitor (Low Power, Low Interest):**
  * **Local Municipality and Community:** Keep an eye on perimeter traffic conditions along roads bordering campus to confirm that detour routing does not push campus congestion into surrounding residential streets.