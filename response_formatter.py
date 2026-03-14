"""
Response Formatter for AI Chat Module
Formats database results into user-friendly responses
"""

from typing import Dict, List, Any


class ResponseFormatter:
    def __init__(self):
        self.intent_responses = {
            "list_freelancers": self._format_list_freelancers,
            "freelancer_detail": self._format_freelancer_detail,
            "freelancer_reviews": self._format_freelancer_reviews,
            "freelancer_portfolio": self._format_freelancer_portfolio,
            "client_hire_requests": self._format_client_hire_requests,
            "client_messages": self._format_client_messages,
            "client_projects": self._format_client_projects,
            "freelancer_hire_requests": self._format_freelancer_hire_requests,
            "freelancer_messages": self._format_freelancer_messages,
            "freelancer_profile": self._format_freelancer_profile
        }
    
    def format_response(self, intent: str, data: List[Dict], original_message: str) -> Dict:
        """Format database results into user-friendly response"""
        try:
            if intent not in self.intent_responses:
                return {
                    "answer": "I couldn't format the response for this type of question.",
                    "data_count": 0
                }
            
            formatter_func = self.intent_responses[intent]
            return formatter_func(data, original_message)
            
        except Exception as e:
            print(f"Error formatting response: {str(e)}")
            return {
                "answer": "I found some results but had trouble formatting them. Please try again.",
                "data_count": len(data) if data else 0
            }
    
    def _format_list_freelancers(self, data: List[Dict], original_message: str) -> Dict:
        """Format list of freelancers"""
        if not data:
            return {
                "answer": "I couldn't find any freelancers matching your criteria.",
                "data_count": 0
            }
        
        count = len(data)
        if count == 1:
            freelancer = data[0]
            name = freelancer.get('name', 'Unknown')
            category = freelancer.get('category', 'Unknown')
            location = freelancer.get('location', 'Unknown')
            rating = freelancer.get('rating', 0)
            
            rating_text = f"with {rating}/5 rating" if rating else "with no rating"
            answer = f"I found 1 freelancer: {name}, a {category} from {location} {rating_text}."
        else:
            # Format multiple freelancers
            names = [f.get('name', 'Unknown') for f in data[:5]]  # Show first 5
            if count <= 5:
                freelancer_list = ", ".join(names)
                answer = f"I found {count} freelancers: {freelancer_list}."
            else:
                freelancer_list = ", ".join(names)
                answer = f"I found {count} freelancers. Here are the top matches: {freelancer_list}..."
        
        return {
            "answer": answer,
            "data_count": count
        }
    
    def _format_freelancer_detail(self, data: List[Dict], original_message: str) -> Dict:
        """Format freelancer details"""
        if not data:
            return {
                "answer": f"I couldn't find a freelancer matching that name.",
                "data_count": 0
            }
        
        freelancer = data[0]
        name = freelancer.get('name', 'Unknown')
        category = freelancer.get('category', 'Unknown')
        location = freelancer.get('location', 'Unknown')
        rating = freelancer.get('rating', 0)
        budget_min = freelancer.get('min_budget', 'Not specified')
        budget_max = freelancer.get('max_budget', 'Not specified')
        experience = freelancer.get('experience', 'Not specified')
        
        answer = f"I found {name}, a {category} from {location}. "
        if rating:
            answer += f"Rating: {rating}/5. "
        if experience and experience != 'Not specified':
            answer += f"Experience: {experience} years. "
        if budget_min != 'Not specified' and budget_max != 'Not specified':
            answer += f"Budget range: ₹{budget_min} - ₹{budget_max}."
        
        return {
            "answer": answer,
            "data_count": 1
        }
    
    def _format_freelancer_reviews(self, data: List[Dict], original_message: str) -> Dict:
        """Format freelancer reviews"""
        if not data:
            return {
                "answer": "I couldn't find any reviews for this freelancer.",
                "data_count": 0
            }
        
        count = len(data)
        if count == 1:
            review = data[0]
            rating = review.get('rating', 'No rating')
            client_name = review.get('client_name', 'Anonymous')
            answer = f"I found 1 review from {client_name} with a {rating}/5 rating."
        else:
            avg_rating = sum(r.get('rating', 0) for r in data) / count
            answer = f"I found {count} reviews with an average rating of {avg_rating:.1f}/5."
        
        return {
            "answer": answer,
            "data_count": count
        }
    
    def _format_freelancer_portfolio(self, data: List[Dict], original_message: str) -> Dict:
        """Format freelancer portfolio"""
        if not data:
            return {
                "answer": "I couldn't find any portfolio items for this freelancer.",
                "data_count": 0
            }
        
        count = len(data)
        if count == 1:
            item = data[0]
            title = item.get('title', 'Untitled')
            answer = f"I found 1 portfolio item: {title}."
        else:
            titles = [item.get('title', 'Untitled') for item in data[:3]]
            if count <= 3:
                portfolio_list = ", ".join(titles)
                answer = f"I found {count} portfolio items: {portfolio_list}."
            else:
                portfolio_list = ", ".join(titles)
                answer = f"I found {count} portfolio items. Recent work includes: {portfolio_list}..."
        
        return {
            "answer": answer,
            "data_count": count
        }
    
    def _format_client_hire_requests(self, data: List[Dict], original_message: str) -> Dict:
        """Format client hire requests"""
        if not data:
            return {
                "answer": "You don't have any hire requests yet.",
                "data_count": 0
            }
        
        count = len(data)
        active_count = sum(1 for req in data if req.get('status') in ['pending', 'accepted'])
        
        if count == 1:
            req = data[0]
            title = req.get('project_title', 'Untitled project')
            status = req.get('status', 'Unknown')
            freelancer = req.get('freelancer_name', 'Unknown')
            answer = f"You have 1 hire request: '{title}' with {freelancer} (Status: {status})."
        else:
            answer = f"You have {count} hire requests, with {active_count} active requests."
        
        return {
            "answer": answer,
            "data_count": count
        }
    
    def _format_client_messages(self, data: List[Dict], original_message: str) -> Dict:
        """Format client messages"""
        if not data:
            return {
                "answer": "You don't have any messages yet.",
                "data_count": 0
            }
        
        count = len(data)
        unique_senders = len(set(msg.get('sender_name', 'Unknown') for msg in data))
        
        if count == 1:
            msg = data[0]
            sender = msg.get('sender_name', 'Unknown')
            preview = (msg.get('message', '')[:50] + '...') if len(msg.get('message', '')) > 50 else msg.get('message', '')
            answer = f"You have 1 message from {sender}: \"{preview}\""
        else:
            answer = f"You have {count} messages from {unique_senders} different people."
        
        return {
            "answer": answer,
            "data_count": count
        }
    
    def _format_client_projects(self, data: List[Dict], original_message: str) -> Dict:
        """Format client projects"""
        if not data:
            return {
                "answer": "You haven't posted any projects yet.",
                "data_count": 0
            }
        
        count = len(data)
        active_count = sum(1 for project in data if project.get('status') in ['open', 'active'])
        
        if count == 1:
            project = data[0]
            title = project.get('title', 'Untitled project')
            status = project.get('status', 'Unknown')
            budget = project.get('budget', 'Not specified')
            answer = f"You have 1 project: '{title}' with budget ₹{budget} (Status: {status})."
        else:
            answer = f"You have {count} posted projects, with {active_count} currently active."
        
        return {
            "answer": answer,
            "data_count": count
        }
    
    def _format_freelancer_hire_requests(self, data: List[Dict], original_message: str) -> Dict:
        """Format freelancer hire requests"""
        if not data:
            return {
                "answer": "You don't have any hire requests yet.",
                "data_count": 0
            }
        
        count = len(data)
        active_count = sum(1 for req in data if req.get('status') in ['pending', 'accepted'])
        
        if count == 1:
            req = data[0]
            title = req.get('project_title', 'Untitled project')
            status = req.get('status', 'Unknown')
            client = req.get('client_name', 'Unknown')
            answer = f"You have 1 hire request: '{title}' from {client} (Status: {status})."
        else:
            answer = f"You have {count} hire requests, with {active_count} active requests."
        
        return {
            "answer": answer,
            "data_count": count
        }
    
    def _format_freelancer_messages(self, data: List[Dict], original_message: str) -> Dict:
        """Format freelancer messages"""
        if not data:
            return {
                "answer": "You don't have any messages yet.",
                "data_count": 0
            }
        
        count = len(data)
        unique_senders = len(set(msg.get('sender_name', 'Unknown') for msg in data))
        
        if count == 1:
            msg = data[0]
            sender = msg.get('sender_name', 'Unknown')
            preview = (msg.get('message', '')[:50] + '...') if len(msg.get('message', '')) > 50 else msg.get('message', '')
            answer = f"You have 1 message from {sender}: \"{preview}\""
        else:
            answer = f"You have {count} messages from {unique_senders} different people."
        
        return {
            "answer": answer,
            "data_count": count
        }
    
    def _format_freelancer_profile(self, data: List[Dict], original_message: str) -> Dict:
        """Format freelancer's own profile"""
        if not data:
            return {
                "answer": "I couldn't find your profile information.",
                "data_count": 0
            }
        
        freelancer = data[0]
        name = freelancer.get('name', 'Unknown')
        category = freelancer.get('category', 'Unknown')
        location = freelancer.get('location', 'Unknown')
        rating = freelancer.get('rating', 0)
        budget_min = freelancer.get('min_budget', 'Not specified')
        budget_max = freelancer.get('max_budget', 'Not specified')
        experience = freelancer.get('experience', 'Not specified')
        
        answer = f"Your profile: {name}, a {category} from {location}. "
        if rating:
            answer += f"Your rating is {rating}/5. "
        if experience and experience != 'Not specified':
            answer += f"Experience: {experience} years. "
        if budget_min != 'Not specified' and budget_max != 'Not specified':
            answer += f"Budget range: ₹{budget_min} - ₹{budget_max}."
        
        return {
            "answer": answer,
            "data_count": 1
        }
