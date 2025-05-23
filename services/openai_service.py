import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage
from azure.core.credentials import AzureKeyCredential
import autogen
from agents import Agent, MultiAgentSystem
from config import settings
from models import UserStory, AcceptanceCriteria

logger = logging.getLogger(__name__)


class Agent:
    """Base agent class for AI-powered tasks"""
    
    def __init__(self, name: str, description: str, llm_client):
        self.name = name
        self.description = description
        self.llm_client = llm_client
        self.memory = []
    
    async def execute_task(self, system_prompt: str, user_prompt: str) -> str:
        """Execute a task using the LLM client"""
        try:
            if hasattr(self.llm_client, 'chat') and hasattr(self.llm_client.chat, 'completions'):
                # Standard OpenAI client
                response = await self.llm_client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=settings.agent_temperature,
                    max_tokens=1500
                )
                return response.choices[0].message.content
            
            elif hasattr(self.llm_client, 'complete'):
                # Azure AI Inference client
                messages = [
                    SystemMessage(content=system_prompt),
                    UserMessage(content=user_prompt)
                ]
                
                response = await self.llm_client.complete(
                    messages=messages,
                    model=settings.azure_openai_deployment or settings.openai_model,
                    temperature=settings.agent_temperature,
                    max_tokens=1500
                )
                return response.choices[0].message.content
            
            else:
                # Fallback for other client types
                raise NotImplementedError("Unsupported LLM client type")
                
        except Exception as e:
            logger.error(f"Error executing task for agent {self.name}: {str(e)}")
            raise
    
    def add_to_memory(self, interaction: Dict[str, Any]):
        """Add interaction to agent memory"""
        self.memory.append(interaction)
        # Keep only last 10 interactions to manage memory
        if len(self.memory) > 10:
            self.memory.pop(0)


class MultiAgentSystem:
    """System for managing multiple agents"""
    
    def __init__(self):
        self.agents = {}
        self.conversation_history = []
    
    def add_agent(self, agent: Agent):
        """Add an agent to the system"""
        self.agents[agent.name] = agent
        logger.info(f"Added agent '{agent.name}' to the system")
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get an agent by name"""
        return self.agents.get(name)
    
    async def execute_multi_agent_task(self, task_description: str, required_agents: List[str]) -> Dict[str, Any]:
        """Execute a task that requires multiple agents"""
        results = {}
        
        for agent_name in required_agents:
            agent = self.get_agent(agent_name)
            if agent:
                try:
                    # This would be expanded for more complex multi-agent interactions
                    results[agent_name] = {"status": "ready", "agent": agent}
                except Exception as e:
                    logger.error(f"Error with agent {agent_name}: {str(e)}")
                    results[agent_name] = {"status": "error", "error": str(e)}
            else:
                results[agent_name] = {"status": "not_found"}
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all agents in the system"""
        return {
            "total_agents": len(self.agents),
            "agent_names": list(self.agents.keys()),
            "conversation_history_length": len(self.conversation_history)
        }


class FeatureGeneratorAgent(Agent):
    """Agent specialized in generating features for epics"""
    
    def __init__(self, llm_client):
        super().__init__(
            name="feature_generator",
            description="Generates comprehensive features for software epics based on requirements",
            llm_client=llm_client
        )
    
    async def generate_features(self, epic_title: str, epic_description: str, project_context: str = "") -> List[str]:
        """Generate features for an epic"""
        system_prompt = """You are an expert agile project manager specializing in feature breakdown. 
        Your task is to analyze epics and generate comprehensive, actionable features.
        
        Guidelines:
        - Generate 5-8 specific, actionable features
        - Each feature should be clearly defined and valuable to end users
        - Features should be feasible to implement and testable
        - Consider user experience, technical requirements, and business value
        - Output only the feature list, one feature per line, without numbering"""
        
        user_prompt = f"""
        Epic Title: {epic_title}
        Epic Description: {epic_description}
        Project Context: {project_context}
        
        Generate comprehensive features for this epic:
        """
        
        response = await self.execute_task(system_prompt, user_prompt)
        return self._parse_features_response(response)
    
    def _parse_features_response(self, content: str) -> List[str]:
        """Parse features from agent response"""
        try:
            lines = content.strip().split('\n')
            features = []
            
            for line in lines:
                line = line.strip()
                # Remove common numbering patterns
                line = line.lstrip('0123456789.-• ')
                if line and len(line) > 10:  # Minimum feature length
                    features.append(line)
            
            return features[:8]  # Limit to 8 features max
            
        except Exception as e:
            logger.error(f"Error parsing features response: {str(e)}")
            return []


class UserStoryGeneratorAgent(Agent):
    """Agent specialized in generating user stories with acceptance criteria"""
    
    def __init__(self, llm_client):
        super().__init__(
            name="story_generator",
            description="Creates detailed user stories with acceptance criteria for features",
            llm_client=llm_client
        )
    
    async def generate_user_story(self, epic_description: str, feature: str, project_context: str = "") -> UserStory:
        """Generate a user story for a specific feature"""
        system_prompt = """You are an expert agile project manager specialized in writing user stories.
        Create detailed user stories with proper acceptance criteria following agile best practices.
        
        Guidelines:
        - Follow the format: "As a [user type], I want [functionality] so that [benefit]"
        - Include 3-5 specific, testable acceptance criteria
        - Assign appropriate story points (1, 2, 3, 5, 8, 13)
        - Set realistic priority levels
        - Ensure stories are independent, negotiable, valuable, estimable, small, and testable (INVEST)
        
        Respond with a valid JSON object only:"""
        
        user_prompt = f"""
        Epic Description: {epic_description}
        Feature: {feature}
        Project Context: {project_context}
        
        Create a user story in this JSON format:
        {{
            "title": "Brief title for the user story",
            "description": "As a [user type], I want [functionality] so that [benefit]",
            "acceptance_criteria": [
                {{"criterion": "Specific acceptance criterion 1", "priority": "Must"}},
                {{"criterion": "Specific acceptance criterion 2", "priority": "Should"}},
                {{"criterion": "Specific acceptance criterion 3", "priority": "Could"}}
            ],
            "story_points": 3,
            "priority": "Medium"
        }}
        """
        
        response = await self.execute_task(system_prompt, user_prompt)
        return self._parse_user_story_response(response, feature)
    
    def _parse_user_story_response(self, content: str, feature: str) -> UserStory:
        """Parse user story from agent response"""
        try:
            # Try to extract JSON from the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                story_data = json.loads(json_content)
                
                # Convert acceptance criteria
                acceptance_criteria = []
                if 'acceptance_criteria' in story_data:
                    for criteria in story_data['acceptance_criteria']:
                        acceptance_criteria.append(
                            AcceptanceCriteria(
                                criterion=criteria.get('criterion', ''),
                                priority=criteria.get('priority', 'Should')
                            )
                        )
                
                return UserStory(
                    title=story_data.get('title', f'User story for {feature}'),
                    description=story_data.get('description', ''),
                    story_points=story_data.get('story_points', 3),
                    priority=story_data.get('priority', 'Medium'),
                    acceptance_criteria=acceptance_criteria
                )
            
            else:
                # Fallback: create a basic user story
                return UserStory(
                    title=f"User story for {feature}",
                    description=f"As a user, I want {feature.lower()} so that I can benefit from this functionality.",
                    story_points=3,
                    priority="Medium"
                )
                
        except Exception as e:
            logger.error(f"Error parsing user story response: {str(e)}")
            # Return a basic user story as fallback
            return UserStory(
                title=f"User story for {feature}",
                description=f"As a user, I want {feature.lower()} so that I can benefit from this functionality.",
                story_points=3,
                priority="Medium"
            )


class MeetingNotesProcessorAgent(Agent):
    """Agent specialized in processing meeting notes and creating structured documentation"""
    
    def __init__(self, llm_client):
        super().__init__(
            name="meeting_notes_processor",
            description="Processes raw meeting notes and creates structured Confluence documentation",
            llm_client=llm_client
        )
    
    async def process_meeting_notes(self, meeting_title: str, meeting_date: str, attendees: List[str], 
                                   raw_notes: str, transcript: str = "") -> Dict[str, Any]:
        """Process meeting notes and create structured content for Confluence"""
        system_prompt = """You are an expert meeting facilitator and documentation specialist.
        Your task is to process raw meeting notes and transcripts to create professional, structured documentation.
        
        Guidelines:
        - Extract key discussion points, decisions, and action items
        - Create clear sections: Summary, Key Points, Decisions, Action Items, Next Steps
        - Use professional tone suitable for business documentation
        - Identify participants and their contributions when possible
        - Create follow-up items with clear ownership
        - Structure content for easy reading and reference
        
        Respond with a JSON object containing structured sections:"""
        
        attendees_list = ", ".join(attendees) if attendees else "Not specified"
        
        user_prompt = f"""
        Meeting Title: {meeting_title}
        Meeting Date: {meeting_date}
        Attendees: {attendees_list}
        
        Raw Notes:
        {raw_notes}
        
        Transcript:
        {transcript}
        
        Create structured meeting documentation in this JSON format:
        {{
            "title": "Meeting title for Confluence page",
            "summary": "Brief meeting summary (2-3 sentences)",
            "key_points": [
                "Key discussion point 1",
                "Key discussion point 2"
            ],
            "decisions": [
                "Decision 1 with context",
                "Decision 2 with context"
            ],
            "action_items": [
                {{"item": "Action item description", "owner": "Person responsible", "due_date": "Date or timeframe"}},
                {{"item": "Another action item", "owner": "Person responsible", "due_date": "Date or timeframe"}}
            ],
            "next_steps": [
                "Next step 1",
                "Next step 2"
            ],
            "tags": ["tag1", "tag2", "tag3"]
        }}
        """
        
        response = await self.execute_task(system_prompt, user_prompt)
        return self._parse_meeting_notes_response(response)
    
    def _parse_meeting_notes_response(self, content: str) -> Dict[str, Any]:
        """Parse meeting notes processing response"""
        try:
            # Try to extract JSON from the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                return json.loads(json_content)
            
            else:
                # Fallback: create basic structure
                return {
                    "title": "Meeting Notes",
                    "summary": "Meeting notes processed automatically",
                    "key_points": ["Meeting content processed"],
                    "decisions": [],
                    "action_items": [],
                    "next_steps": [],
                    "tags": ["meeting", "notes"]
                }
                
        except Exception as e:
            logger.error(f"Error parsing meeting notes response: {str(e)}")
            return {
                "title": "Meeting Notes",
                "summary": "Error processing meeting notes",
                "key_points": [],
                "decisions": [],
                "action_items": [],
                "next_steps": [],
                "tags": ["meeting", "error"]
            }
    
    async def create_confluence_content(self, processed_notes: Dict[str, Any], 
                                       meeting_date: str, attendees: List[str]) -> str:
        """Create formatted Confluence page content from processed notes"""
        try:
            title = processed_notes.get("title", "Meeting Notes")
            summary = processed_notes.get("summary", "")
            key_points = processed_notes.get("key_points", [])
            decisions = processed_notes.get("decisions", [])
            action_items = processed_notes.get("action_items", [])
            next_steps = processed_notes.get("next_steps", [])
            
            # Create Confluence-formatted content
            content = f"""h1. {title}

*Date:* {meeting_date}
*Attendees:* {', '.join(attendees) if attendees else 'Not specified'}

h2. Summary
{summary}

"""
            
            if key_points:
                content += "h2. Key Discussion Points\n"
                for point in key_points:
                    content += f"* {point}\n"
                content += "\n"
            
            if decisions:
                content += "h2. Decisions Made\n"
                for decision in decisions:
                    content += f"* {decision}\n"
                content += "\n"
            
            if action_items:
                content += "h2. Action Items\n"
                content += "|| Item || Owner || Due Date ||\n"
                for item in action_items:
                    item_text = item.get("item", "") if isinstance(item, dict) else str(item)
                    owner = item.get("owner", "TBD") if isinstance(item, dict) else "TBD"
                    due_date = item.get("due_date", "TBD") if isinstance(item, dict) else "TBD"
                    content += f"| {item_text} | {owner} | {due_date} |\n"
                content += "\n"
            
            if next_steps:
                content += "h2. Next Steps\n"
                for step in next_steps:
                    content += f"* {step}\n"
                content += "\n"
            
            content += f"----\n_This page was automatically generated from meeting notes on {datetime.now().strftime('%Y-%m-%d %H:%M')}_"
            
            return content
            
        except Exception as e:
            logger.error(f"Error creating Confluence content: {str(e)}")
            return f"# {processed_notes.get('title', 'Meeting Notes')}\n\nError creating formatted content."


class OpenAIService:
    """Service for interacting with AI models using agents framework"""
    
    def __init__(self):
        self._initialize_client()
        self._initialize_agents()
    
    def _initialize_client(self):
        """Initialize the appropriate AI client (Azure OpenAI or OpenAI)"""
        try:
            if settings.use_azure_openai and settings.azure_openai_endpoint:
                # Use Azure OpenAI
                self.client = ChatCompletionsClient(
                    endpoint=settings.azure_openai_endpoint,
                    credential=AzureKeyCredential(settings.azure_openai_api_key)
                )
                self.model = settings.azure_openai_deployment or settings.openai_model
                logger.info("Initialized Azure OpenAI client")
            else:
                # Use standard OpenAI
                self.client = AsyncOpenAI(api_key=settings.openai_api_key)
                self.model = settings.openai_model
                logger.info("Initialized OpenAI client")
                
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {str(e)}")
            raise
    
    def _initialize_agents(self):
        """Initialize specialized agents"""
        try:
            # Initialize agent system
            self.agent_system = MultiAgentSystem()
            
            # Create specialized agents
            self.feature_agent = FeatureGeneratorAgent(self.client)
            self.story_agent = UserStoryGeneratorAgent(self.client)
            self.meeting_notes_agent = MeetingNotesProcessorAgent(self.client)
            
            # Add agents to the system
            self.agent_system.add_agent(self.feature_agent)
            self.agent_system.add_agent(self.story_agent)
            self.agent_system.add_agent(self.meeting_notes_agent)
            
            logger.info("Successfully initialized AI agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            raise
    
    async def generate_features(self, epic_title: str, epic_description: str, project_context: str = "") -> List[str]:
        """
        Generate features for an epic using the feature generator agent
        
        Args:
            epic_title: Title of the epic
            epic_description: Description of the epic
            project_context: Additional context about the project
            
        Returns:
            List of generated features
        """
        try:
            features = await self.feature_agent.generate_features(
                epic_title=epic_title,
                epic_description=epic_description,
                project_context=project_context
            )
            
            logger.info(f"Generated {len(features)} features for epic: {epic_title}")
            return features
            
        except Exception as e:
            logger.error(f"Error generating features: {str(e)}")
            return []
    
    async def generate_user_stories(
        self, 
        epic_description: str, 
        features: List[str], 
        project_context: str = ""
    ) -> List[UserStory]:
        """
        Generate user stories using the story generator agent
        
        Args:
            epic_description: Description of the epic
            features: List of features to create stories for
            project_context: Additional project context
            
        Returns:
            List of generated user stories
        """
        try:
            user_stories = []
            
            # Generate stories concurrently for better performance
            tasks = []
            for feature in features:
                task = self.story_agent.generate_user_story(
                    epic_description=epic_description,
                    feature=feature,
                    project_context=project_context
                )
                tasks.append(task)
            
            # Execute all tasks concurrently
            generated_stories = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and add valid stories
            for i, result in enumerate(generated_stories):
                if isinstance(result, UserStory):
                    user_stories.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Error generating story for feature '{features[i]}': {str(result)}")
            
            logger.info(f"Generated {len(user_stories)} user stories from {len(features)} features")
            return user_stories
            
        except Exception as e:
            logger.error(f"Error generating user stories: {str(e)}")
            return []
    
    async def process_meeting_notes(self, meeting_title: str, meeting_date: str, 
                                   attendees: List[str], raw_notes: str, transcript: str = "") -> Dict[str, Any]:
        """
        Process meeting notes using the meeting notes processor agent
        
        Args:
            meeting_title: Title of the meeting
            meeting_date: Date of the meeting
            attendees: List of meeting attendees
            raw_notes: Raw meeting notes content
            transcript: Meeting transcript (optional)
            
        Returns:
            Structured meeting content
        """
        try:
            processed_notes = await self.meeting_notes_agent.process_meeting_notes(
                meeting_title=meeting_title,
                meeting_date=meeting_date,
                attendees=attendees,
                raw_notes=raw_notes,
                transcript=transcript
            )
            
            logger.info(f"Successfully processed meeting notes for: {meeting_title}")
            return processed_notes
            
        except Exception as e:
            logger.error(f"Error processing meeting notes: {str(e)}")
            return {
                "title": meeting_title,
                "summary": "Error processing meeting notes",
                "key_points": [],
                "decisions": [],
                "action_items": [],
                "next_steps": [],
                "tags": ["meeting", "error"]
            }
    
    async def create_confluence_content_from_meeting(self, processed_notes: Dict[str, Any], 
                                                   meeting_date: str, attendees: List[str]) -> str:
        """
        Create Confluence page content from processed meeting notes
        
        Args:
            processed_notes: Structured meeting notes
            meeting_date: Meeting date
            attendees: List of attendees
            
        Returns:
            Formatted Confluence content
        """
        try:
            content = await self.meeting_notes_agent.create_confluence_content(
                processed_notes=processed_notes,
                meeting_date=meeting_date,
                attendees=attendees
            )
            
            logger.info("Successfully created Confluence content from meeting notes")
            return content
            
        except Exception as e:
            logger.error(f"Error creating Confluence content: {str(e)}")
            return f"# {processed_notes.get('title', 'Meeting Notes')}\n\nError creating formatted content."
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status information about the agents"""
        try:
            return {
                "feature_agent": {
                    "name": self.feature_agent.name,
                    "description": self.feature_agent.description,
                    "status": "active"
                },
                "story_agent": {
                    "name": self.story_agent.name,
                    "description": self.story_agent.description,
                    "status": "active"
                },
                "meeting_notes_agent": {
                    "name": self.meeting_notes_agent.name,
                    "description": self.meeting_notes_agent.description,
                    "status": "active"
                },
                "agent_system": {
                    "total_agents": len(self.agent_system.agents) if hasattr(self.agent_system, 'agents') else 3,
                    "status": "initialized"
                }
            }
        except Exception as e:
            logger.error(f"Error getting agent status: {str(e)}")
            return {"error": str(e)}
    
    async def close(self):
        """Clean up resources"""
        try:
            if hasattr(self.client, 'close'):
                await self.client.close()
            logger.info("AI service resources cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up AI service: {str(e)}") 