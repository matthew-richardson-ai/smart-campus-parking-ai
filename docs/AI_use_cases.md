# CSC 4610 Software Engineering: AI Lab #2 - Use Case Evaluation

---

## 1. Use Case Description
* **Project Concept:** A smart campus parking and rideshare optimization platform built to reduce traffic congestion without constructing new physical parking infrastructure.
* **Core Functionality:** The system connects to existing campus security cameras using edge computer vision to monitor real-time lot occupancy. It uses machine learning to analyze historical turnover alongside class schedules to forecast where and when spots open up. Drivers receive dynamic rerouting updates before arriving at full lots, while an automated carpool engine groups nearby students based on their class times and home locations.

---

## 2. Motivation[cite: 1]
* **Category:** Productivity Opportunity with exploratory elements.
* **Operational Justification:** Students and faculty spend 15 to 30 minutes circling full parking lots each morning, which leads to late arrivals, campus roadway backups, and wasted fuel. Finding spaces faster and putting more students into fewer cars directly gives that lost instructional and study time back to campus. Because expanding physical parking lots is financially and geographically impossible, optimizing current infrastructure through software is an operational necessity[cite: 1].

---

## 3. Build vs. Buy[cite: 1]
* **Strategy:** Hybrid Integration (Buy standard infrastructure, build custom campus intelligence)[cite: 1].
* **What to Buy:**
  * Base computer vision models from the open-source YOLO family running on local edge hardware instead of training vision architectures from scratch.
  * Commercial mapping and navigation APIs (e.g., Mapbox, Google Maps Platform) for standard turn-by-turn routing and mapping data.
  * Notification endpoints (e.g., Firebase Cloud Messaging, Twilio) to handle user alerts.
* **What to Build:**
  * Custom turnover prediction models trained specifically on university bell schedules and historical lot vacate rates.
  * Camera pipeline tailored to campus lens angles, mounting heights, and blind spots.
  * Privacy-preserving spatial clustering engine that matches student routes without exposing raw home addresses.

---

## 4. Human-in-the-Loop[cite: 1]
* **Automation Level:** Partial Automation.
* **Current Lifecycle Stage:** Walk Stage[cite: 1].
* **Operational Phases:**
  * **Crawl Phase:** The system provides passive advice[cite: 1]. It suggests open parking areas and lists potential carpool partners, leaving all routing choices, confirmations, and scheduling to the user.
  * **Walk Phase:** The system automatically calculates and offers in-route reroutes when a primary lot nears 90% capacity. Drivers can accept or dismiss the route with one tap. Users also confirm departures to help validate camera sensor counts.
  * **Run Phase:** In-transit reroutes become fully automated defaults unless explicitly overridden, and carpool groups dynamically rebalance if someone drops out[cite: 1].

---

## 5. Success Metrics[cite: 1]
* **Business Impact:**
  * Reduce average time spent searching for a parking space from roughly 20 minutes down to under 5 minutes during peak morning rush[cite: 1].
  * Cut the volume of single-occupancy student vehicles driving to campus by 15% through active carpooling[cite: 1].
  * Improve student and faculty satisfaction scores regarding campus transit by at least 25% over baseline surveys[cite: 1].
* **Quality:**
  * Achieve 90% or higher accuracy when forecasting open spots within a 5-minute arrival window[cite: 1].
  * Keep false-positive lot saturation warnings under 5%[cite: 1].
  * Maintain an 85% or higher successful completion rate for scheduled student carpools.
* **Latency:**
  * Camera lot-occupancy status must refresh across the system every 10 seconds or faster[cite: 1].
  * In-flight detour and rerouting alerts must deliver to driver phones within 2 seconds of a lot reaching capacity[cite: 1].
* **Cost:**
  * Keep cloud API and inference serving costs below $0.05 per active user session through edge inference and batched routing calls[cite: 1].
  * Limit hardware costs strictly to mini-edge processing devices tied to existing security cameras, avoiding full lot renovations.

---

## 6. Risks & Challenges
* **Technical Constraints:** Heavy rain, night glare, and dense fog can degrade camera vision accuracy. Peripheral parking lots often have poor cellular data reception, which can delay real-time map updates.
* **Seasonal Demand Shifts:** Traffic patterns fluctuate heavily between the start of a semester, midterms, and finals, requiring regular calibration of turnover models.
* **Privacy and Compliance:** Tracking student locations and matching course schedules requires strict FERPA compliance and data anonymization.
* **User Adoption and Safety:** Students may be hesitant to share rides with people they have not met. Clear verification systems, university account logins, and liability protections are needed before launching the carpool feature.

---

## 7. Final Recommendation
* **Decision:** (2) Pilot
* **Justification:** Moving directly into full campus production carries high operational risks around camera coverage, student privacy, and rideshare trust. A controlled pilot focused on two or three high-traffic commuter lots lets the team test camera pipelines under changing weather, calibrate prediction models against real class dismissals, and observe student carpool retention before committing university resources to a full rollout.