import os
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --------------------------------
# Setup logging
# --------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# --------------------------------
# Load env
# --------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)
logging.info(f"Loaded env from {ENV_PATH}")

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_KEY:
    raise ValueError("❌ SERPAPI_API_KEY missing in .env")

# --------------------------------
# Priority Learning Websites
# --------------------------------
PRIORITY_WEBSITES = [
    "geeksforgeeks.org",
    "interviewbit.com", 
    "simplilearn.com",
    "roadmap.sh",
    "turing.com",
    "leetcode.com",
    "hackerrank.com",
    "codingninjas.com",
    "javatpoint.com",
    "tutorialspoint.com"
]

# --------------------------------
# Roles & Tech Skills
# --------------------------------
ROLE_TECH_MAP: Dict[str, List[str]] = {
      "Quantitative Developer / HFT Developer": [
        "C++","CPP", "Python", "Java", "KDB/Q", "FIX Protocol", "Linux", 
        "Multithreading", "Pandas", "NumPy", "Algorithmic Trading",
        "Time-series Databases", "Performance Optimization"
    ],
    "QA / Test Automation Engineer": [
        "Selenium", "Cypress", "Playwright", "Appium", "JUnit", "PyTest", 
        "TestNG", "Postman", "REST Assured", "Jenkins", "CI/CD", 
        "Automation Frameworks", "Bug Tracking Tools (JIRA)"
    ],
    "Embedded Systems Engineer": [
        "C", "C++", "Embedded C", "ARM Cortex", "RTOS", "Arduino", 
        "Raspberry Pi", "Assembly", "Device Drivers", "Firmware Development", 
        "IoT Protocols", "Linux"
    ],
    "Game Developer": [
        "Unity", "Unreal Engine", "C#", "C++", "OpenGL", "DirectX", 
        "Blender", "3D Modeling", "Shaders", "Animation Systems", 
        "Multiplayer Networking", "VR/AR Development"
    ],
    "Robotics Engineer": [
        "ROS (Robot Operating System)", "Gazebo", "C++", "Python", "MATLAB", 
        "LiDAR", "SLAM", "Path Planning", "Motion Control", "Arduino", 
        "Jetson Nano", "Computer Vision", "OpenCV"],
    "AI/ML Architect": ["Python", "TensorFlow", "PyTorch", "Kubernetes", "AWS SageMaker", "MLOps", "Scikit-learn", "Docker", "Apache Spark", "NumPy", "Pandas", "Jupyter", "Git", "Linux", "Deep Learning", "Computer Vision", "NLP", "Model Deployment", "Feature Engineering", "Statistical Analysis", "XGBoost", "Hugging Face", "ONNX", "Microservices", "REST API"],
    "Data Scientist": ["Python", "R", "SQL", "Scikit-learn", "Pandas", "Statistics", "NumPy", "Matplotlib", "Seaborn", "Jupyter", "Machine Learning", "Deep Learning", "Statistical Modeling", "Hypothesis Testing", "A/B Testing", "Time Series Analysis", "Feature Engineering", "Data Visualization", "Git", "Excel", "Tableau", "TensorFlow", "XGBoost", "Apache Spark", "AWS"],
    "Data Engineer": ["SQL", "Python", "Apache Spark", "ETL", "Airflow", "Kafka", "Hadoop", "Docker", "Kubernetes", "AWS", "Scala", "Git", "Linux", "PostgreSQL", "MongoDB", "Redis", "Data Warehousing", "Data Lakes", "Databricks", "Snowflake", "Apache Beam", "Terraform", "Jenkins", "Pandas", "NumPy"],
    "Prompt Engineer": ["Generative AI", "LLM", "Prompt Design", "LangChain", "Fine-tuning", "OpenAI API", "Hugging Face", "Python", "Vector Databases", "RAG", "Embeddings", "JSON", "API Integration", "Model Evaluation", "Chain-of-thought", "Few-shot Learning", "Multi-modal AI", "Semantic Search", "Pinecone", "Chroma", "JavaScript", "YAML", "Transformers", "BERT", "GPT"],
    "Big Data Engineer": ["Hadoop", "Apache Spark", "Hive", "Scala", "Big data concepts", "Java", "Python", "Kafka", "HBase", "Cassandra", "HDFS", "MapReduce", "SQL", "ETL", "Databricks", "AWS EMR", "Elasticsearch", "Docker", "Kubernetes", "Linux", "Shell Scripting", "Data Lakes", "Stream Processing", "Apache Flink", "NoSQL"],
    "Business Intelligence (BI) Analyst": ["SQL", "Tableau", "Power BI", "Data Warehousing", "Reporting", "Excel", "Python", "ETL", "Data Modeling", "KPI Development", "Dashboard Design", "SSRS", "SSIS", "Statistical Analysis", "Data Visualization", "QlikView", "Looker", "Crystal Reports", "OLAP", "Star Schema", "SAP BusinessObjects", "Google Analytics", "Forecasting", "Trend Analysis", "Ad-hoc Analysis"],
    "Data Analyst": ["SQL", "Excel", "Python", "Pandas", "Data Visualization", "Tableau", "Power BI", "Statistical Analysis", "NumPy", "Matplotlib", "Seaborn", "R", "Jupyter", "Descriptive Statistics", "Regression Analysis", "Hypothesis Testing", "A/B Testing", "Google Analytics", "Pivot Tables", "Data Cleaning", "Plotly", "VBA", "SPSS", "Looker"],
    "Cloud Architect/Engineer": ["AWS", "Azure", "Google Cloud", "Infrastructure as Code", "Terraform", "CloudFormation", "Docker", "Kubernetes", "Ansible", "Linux", "Networking", "Security", "Monitoring", "Serverless", "Microservices", "API Gateway", "Load Balancing", "VPC", "IAM", "Cost Optimization", "Disaster Recovery", "High Availability", "Multi-cloud", "Containers", "DevOps"],
    "DevOps Engineer": ["CI/CD", "Jenkins", "Docker", "Kubernetes", "Ansible", "Git", "Linux", "AWS", "Azure", "Terraform", "Prometheus", "Grafana", "GitLab CI", "GitHub Actions", "Python", "Bash", "Helm", "Monitoring", "Infrastructure as Code", "Configuration Management", "Containerization", "Microservices", "Load Balancing", "Security", "Automation"],
    "Site Reliability Engineer (SRE)": ["Kubernetes", "Prometheus", "Grafana", "System Design", "Go", "Python", "Linux", "Docker", "Terraform", "Monitoring", "Incident Response", "Load Balancing", "Distributed Systems", "Performance Optimization", "Capacity Planning", "SLI/SLO", "Error Budgets", "Chaos Engineering", "Microservices", "API Design", "Database Optimization", "Caching", "Cloud Platforms", "Infrastructure as Code", "Networking"],
    "Cybersecurity Specialist/Analyst": ["Network Security", "SIEM", "Cryptography", "Penetration Testing", "Firewalls", "IDS/IPS", "Vulnerability Scanners", "Incident Response", "Risk Assessment", "Compliance", "PKI", "Multi-factor Authentication", "IAM", "Threat Intelligence", "Malware Analysis", "Digital Forensics", "Security Frameworks", "Endpoint Protection", "Cloud Security", "Web Application Security", "Wireshark", "Splunk", "Nessus", "ISO 27001", "NIST"],
    "Ethical Hacker/Penetration Tester": ["Metasploit", "Burp Suite", "Nmap", "Kali Linux", "OWASP Top 10", "Wireshark", "SQLmap", "John the Ripper", "Nikto", "Vulnerability Assessment", "Web Application Testing", "Network Penetration Testing", "Social Engineering", "Exploit Development", "Report Writing", "Risk Assessment", "Compliance Testing", "Red Team Operations", "Wireless Security", "Buffer Overflows", "Reverse Engineering", "Custom Exploits", "CVE Analysis", "Security Auditing", "Threat Modeling"],
    "Full-Stack Developer": ["JavaScript", "React", "Node.js", "Express.js", "SQL", "REST API", "HTML5", "CSS3", "TypeScript", "MongoDB", "PostgreSQL", "Git", "Docker", "AWS", "GraphQL", "Redux", "Vue.js", "Angular", "Next.js", "Tailwind CSS", "Jest", "Webpack", "Authentication", "Microservices", "WebSockets"],
    "Software Development Engineer (SDE)": ["Data Structures", "Algorithms", "System Design", "Java", "C++", "Python", "Object-Oriented Programming", "Design Patterns", "Testing", "Git", "Debugging", "Performance Optimization", "Databases", "Networking", "Multithreading", "Clean Code", "SOLID Principles", "Distributed Systems", "API Design", "Microservices", "Code Review", "CI/CD", "Linux", "TDD", "BDD"],
    "Mobile Application Developer": ["Swift", "Kotlin", "React Native", "Flutter", "iOS", "Android", "Objective-C", "Java", "Dart", "UI/UX Design", "API Integration", "Core Data", "SQLite", "Firebase", "Push Notifications", "App Store Optimization", "Testing", "Git", "Performance Optimization", "Security", "Offline Functionality", "Camera Integration", "Location Services", "Biometric Authentication", "Cross-platform Development"],
    "Software Architect": ["System Design", "Microservices", "Design Patterns", "Scalability", "Distributed Systems", "API Design", "Database Design", "Cloud Architecture", "Security Architecture", "Performance Optimization", "High Availability", "Load Balancing", "Caching Strategies", "Enterprise Architecture", "Domain-driven Design", "Event-driven Architecture", "Integration Patterns", "Technology Evaluation", "Architecture Documentation", "Legacy System Modernization", "Message Queues", "CQRS", "Event Sourcing", "Service Mesh", "Monitoring"],
    "Blockchain Developer": ["Solidity", "Ethereum", "Smart Contracts", "Web3.js", "Cryptography", "JavaScript", "TypeScript", "React", "Node.js", "Hardhat", "Truffle", "MetaMask", "IPFS", "DeFi", "NFTs", "Gas Optimization", "Security Auditing", "Rust", "Go", "Bitcoin", "Layer 2 Solutions", "Cross-chain", "Consensus Algorithms", "Wallet Development", "Testing Frameworks"],
    "IT Project Manager": ["Agile", "Scrum", "Project Management", "JIRA", "Risk Management", "Kanban", "Microsoft Project", "Confluence", "Budget Management", "Resource Planning", "Stakeholder Management", "Requirements Gathering", "User Stories", "Sprint Planning", "Change Management", "Quality Assurance", "Vendor Management", "ITIL", "Prince2", "SAFe", "Timeline Management", "Gantt Charts", "Critical Path", "KPI Tracking", "Process Improvement"],
    "UI/UX Designer": ["Figma", "Adobe XD", "User Research", "Wireframing", "Prototyping", "Sketch", "Adobe Creative Suite", "HTML/CSS", "Design Systems", "Typography", "Color Theory", "Responsive Design", "Accessibility", "Usability Testing", "A/B Testing", "Information Architecture", "Journey Mapping", "Persona Development", "Interaction Design", "Motion Graphics", "Component Libraries", "Design Handoff", "User Testing", "Competitive Analysis", "Design Thinking"],
    "Database Administrator (DBA)": ["SQL", "Database Optimization", "Backup and Recovery", "PostgreSQL", "MySQL", "SQL Server", "Oracle", "MongoDB", "Performance Tuning", "Query Optimization", "Index Management", "Database Design", "Replication", "High Availability", "Security Management", "User Access Control", "Monitoring", "Scripting", "Cloud Databases", "Database Migration", "Stored Procedures", "Triggers", "Capacity Planning", "Disaster Recovery", "Compliance"],
    "GenAI Developer / AI Engineer": ["Python", "R","TensorFlow", "PyTorch", "Keras", "Scikit-learn","Transformers", "Hugging Face", "LangChain", "RAG (Retrieval Augmented Generation)",
        "Vector Databases (Pinecone, Weaviate, FAISS)", "OpenAI API", "Anthropic API",
        "Pandas", "NumPy", "SQL", "NoSQL","Docker", "Kubernetes", "FastAPI", "Flask", "Streamlit", "CI/CD", 
        "AWS Sagemaker", "Azure ML", "Google Vertex AI", "GCP","Fine-tuning", "LLM Evaluation", 
        "RLHF (Reinforcement Learning with Human Feedback)"
    ]
}

# --------------------------------
# Search Counter and Budget Management
# --------------------------------
class SearchBudget:
    def __init__(self, max_searches: int = 250):
        self.max_searches = max_searches
        self.used_searches = 0
        self.remaining = max_searches
    
    def can_search(self) -> bool:
        return self.used_searches < self.max_searches
    
    def use_search(self):
        if self.can_search():
            self.used_searches += 1
            self.remaining = self.max_searches - self.used_searches
            return True
        return False
    
    def get_status(self) -> str:
        return f"Used: {self.used_searches}/{self.max_searches} | Remaining: {self.remaining}"

# Global search budget tracker
search_budget = SearchBudget(250)

# --------------------------------
# Optimized SerpAPI Search for Limited Budget
# --------------------------------
def optimized_serpapi_search(query: str, is_priority: bool = False) -> List[str]:
    """Optimized search with budget management"""
    if not search_budget.can_search():
        logging.warning(f"❌ Search budget exhausted! {search_budget.get_status()}")
        return []
    
    try:
        logging.info(f"  🔍 Search ({search_budget.used_searches + 1}/250): {query}")
        
        url = "https://serpapi.com/search"
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 12 if is_priority else 8  # More results for priority searches
        }
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        
        urls = [item["link"] for item in data.get("organic_results", []) if "link" in item]
        search_budget.use_search()
        
        logging.info(f"  ✅ Found {len(urls)} URLs | {search_budget.get_status()}")
        return urls
        
    except Exception as e:
        logging.error(f"  ❌ Search failed: {e}")
        search_budget.use_search()  # Still count failed searches
        return []

def smart_search_for_skill(role: str, skill: str) -> List[str]:
    """Optimized search strategy for budget constraint"""
    all_urls = []
    
    # Single strategic search that combines priority sites with dual approach
    if search_budget.remaining > 20:
        # Use OR operator to search multiple priority sites in one query
        priority_sites = " OR ".join([f"site:{site}" for site in PRIORITY_WEBSITES[:4]])
        query = f"({priority_sites}) {skill} interview questions"
    else:
        # Fallback to direct search when budget is low
        query = f"{skill} interview questions"
    
    # Add role context for better targeting
    if len(role.split()) <= 3:  # Only for shorter role names to avoid long queries
        query = f"{query} {role}"
    
    urls = optimized_serpapi_search(query, is_priority=True)
    all_urls.extend(urls)
    
    return all_urls[:8]  # Limit to manage processing time

# --------------------------------
# Enhanced Q&A Extraction
# --------------------------------
def extract_qa_from_url(url: str) -> List[Dict[str, str]]:
    """Enhanced Q&A extraction with better parsing for various sites"""
    qa_pairs = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        resp = requests.get(url, timeout=15, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()

        # Site-specific extraction strategies
        if "geeksforgeeks.org" in url:
            qa_pairs = extract_qa_geeksforgeeks(soup, url)
        elif "interviewbit.com" in url:
            qa_pairs = extract_qa_interviewbit(soup, url)
        elif any(site in url for site in ["simplilearn.com", "roadmap.sh", "turing.com"]):
            qa_pairs = extract_qa_generic_learning_site(soup, url)
        else:
            qa_pairs = extract_qa_generic(soup, url)
            
        # If site-specific extraction failed, try generic approach
        if not qa_pairs:
            qa_pairs = extract_qa_generic(soup, url)
        
        # Remove duplicates and filter quality
        unique_qas = []
        seen_questions = set()
        for qa in qa_pairs:
            q_lower = qa["question"].lower().strip()
            if (q_lower not in seen_questions and 
                len(qa["question"].split()) >= 3 and
                len(qa["answer"].split()) >= 5):
                seen_questions.add(q_lower)
                unique_qas.append(qa)
        
        return unique_qas[:8]  # Limit per URL to manage data size
        
    except Exception as e:
        logging.warning(f"Failed to scrape {url}: {e}")
        return []

def extract_qa_geeksforgeeks(soup, url: str) -> List[Dict[str, str]]:
    """GeeksforGeeks-specific extraction"""
    qa_pairs = []
    
    try:
        # GFG often uses numbered questions in specific divs
        question_patterns = [
            "h2", "h3", "h4",  # Headers
            ".question", 
            "[class*='question']",
            "strong",
            "b"
        ]
        
        for pattern in question_patterns:
            elements = soup.select(pattern)
            for element in elements:
                text = element.get_text(strip=True)
                
                # Check if it looks like a question
                if ("?" in text and 
                    len(text.split()) >= 3 and 
                    len(text.split()) <= 30):
                    
                    # Try to find answer using multiple strategies
                    answer = None
                    
                    # Strategy 1: Look in next paragraphs
                    next_p = element.find_next("p")
                    if next_p:
                        answer_text = next_p.get_text(strip=True)
                        if answer_text and len(answer_text.split()) >= 5:
                            answer = answer_text
                    
                    # Strategy 2: Look in code blocks (for programming questions)
                    if not answer:
                        next_code = element.find_next(["pre", "code"])
                        if next_code:
                            code_text = next_code.get_text(strip=True)
                            # Look for explanation after code
                            explanation = next_code.find_next("p")
                            if explanation:
                                answer = explanation.get_text(strip=True)
                            elif code_text and len(code_text.split()) >= 3:
                                answer = f"Code solution: {code_text}"
                    
                    # Strategy 3: Look in same container
                    if not answer:
                        container = element.find_parent(["div", "section", "article"])
                        if container:
                            paras = container.find_all("p")
                            for para in paras:
                                para_text = para.get_text(strip=True)
                                if (para_text and len(para_text.split()) >= 5 and 
                                    para != element and not "?" in para_text):
                                    answer = para_text
                                    break
                    
                    if answer:
                        qa_pairs.append({
                            "question": text,
                            "answer": answer[:1000],
                            "source": url
                        })
        
        # Try structured content extraction
        content_div = soup.find("div", {"class": "content"}) or soup.find("article")
        if content_div and not qa_pairs:
            # Look for Q: A: patterns
            all_text = content_div.get_text()
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            
            current_question = None
            for line in lines:
                if (line.startswith(("Q:", "Question:", "Q.", "Q ")) or 
                    ("?" in line and len(line.split()) <= 25)):
                    current_question = line.replace("Q:", "").replace("Question:", "").strip()
                elif (current_question and 
                      (line.startswith(("A:", "Answer:", "A.", "A ")) or 
                       (len(line.split()) >= 5 and not "?" in line))):
                    answer = line.replace("A:", "").replace("Answer:", "").strip()
                    if answer and len(answer.split()) >= 5:
                        qa_pairs.append({
                            "question": current_question,
                            "answer": answer[:1000],
                            "source": url
                        })
                        current_question = None
                        
    except Exception as e:
        logging.warning(f"Error in GeeksforGeeks extraction: {e}")
    
    return qa_pairs

def extract_qa_interviewbit(soup, url: str) -> List[Dict[str, str]]:
    """InterviewBit-specific extraction"""
    qa_pairs = []
    
    try:
        # InterviewBit often has structured Q&A sections
        qa_sections = soup.find_all(["div", "section"], class_=lambda x: x and any(
            keyword in x.lower() for keyword in ["question", "qa", "interview", "problem"]
        ))
        
        for section in qa_sections:
            questions = section.find_all(["h3", "h4", "h5", "strong", "b"])
            for q_elem in questions:
                q_text = q_elem.get_text(strip=True)
                if "?" in q_text and len(q_text.split()) >= 3:
                    # Look for answer in next elements
                    answer_elem = q_elem.find_next(["p", "div", "pre"])
                    if answer_elem:
                        answer = answer_elem.get_text(strip=True)
                        if answer and len(answer.split()) >= 5:
                            qa_pairs.append({
                                "question": q_text,
                                "answer": answer[:1000],
                                "source": url
                            })
                            
    except Exception as e:
        logging.warning(f"Error in InterviewBit extraction: {e}")
    
    return qa_pairs

def extract_qa_generic_learning_site(soup, url: str) -> List[Dict[str, str]]:
    """Generic extraction for learning sites"""
    qa_pairs = []
    
    try:
        # Common patterns for learning sites
        main_content = (soup.find("main") or 
                       soup.find("div", {"class": "content"}) or 
                       soup.find("article") or 
                       soup.body)
        
        if main_content:
            # Look for questions in headers and bold text
            question_elements = main_content.find_all(["h2", "h3", "h4", "h5", "strong", "b"])
            
            for q_elem in question_elements:
                q_text = q_elem.get_text(strip=True)
                if ("?" in q_text and 
                    3 <= len(q_text.split()) <= 30 and
                    not any(skip in q_text.lower() for skip in ["what is this", "how to", "where to"])):
                    
                    # Find answer by looking at following content
                    answer = ""
                    current = q_elem
                    
                    # Check next 5 elements for answer
                    for _ in range(5):
                        if current:
                            next_elem = current.find_next(["p", "div", "li", "pre"])
                            if next_elem:
                                text = next_elem.get_text(strip=True)
                                # Skip if it's another question
                                if "?" not in text and len(text.split()) >= 5:
                                    answer = text
                                    break
                                current = next_elem
                            else:
                                break
                        else:
                            break
                    
                    if answer:
                        qa_pairs.append({
                            "question": q_text,
                            "answer": answer[:1000],
                            "source": url
                        })
                        
    except Exception as e:
        logging.warning(f"Error in generic learning site extraction: {e}")
    
    return qa_pairs

def extract_qa_generic(soup, url: str) -> List[Dict[str, str]]:
    """Fallback generic extraction method"""
    qa_pairs = []
    
    try:
        # Simple approach: find all potential questions and answers
        all_elements = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "strong", "b"])
        
        current_question = None
        for element in all_elements:
            text = element.get_text(strip=True)
            
            if not text or len(text) > 500:  # Skip very long text
                continue
                
            # Identify questions
            if ("?" in text and 
                3 <= len(text.split()) <= 25 and
                element.name in ["h1", "h2", "h3", "h4", "h5", "h6", "strong", "b"]):
                current_question = text
                
            # Identify answers
            elif (current_question and 
                  len(text.split()) >= 5 and 
                  "?" not in text and
                  element.name in ["p", "li", "div"]):
                qa_pairs.append({
                    "question": current_question,
                    "answer": text[:1000],
                    "source": url
                })
                current_question = None
                
                if len(qa_pairs) >= 10:  # Limit to avoid too much data
                    break
                    
    except Exception as e:
        logging.warning(f"Error in generic extraction: {e}")
    
    return qa_pairs

def extract_qa_from_section(section, url: str) -> List[Dict[str, str]]:
    """Extract Q&A pairs from FAQ-like sections"""
    qa_pairs = []
    
    # Look for dt/dd pairs (definition lists)
    dt_elements = section.find_all("dt")
    for dt in dt_elements:
        question = dt.get_text(strip=True)
        dd = dt.find_next_sibling("dd")
        if dd and "?" in question:
            answer = dd.get_text(strip=True)
            if answer and len(answer.split()) >= 5:
                qa_pairs.append({
                    "question": question,
                    "answer": answer,
                    "source": url
                })
    
    # Look for alternating question/answer patterns
    all_elements = section.find_all(["h3", "h4", "h5", "p", "div", "li"])
    current_question = None
    
    for elem in all_elements:
        text = elem.get_text(strip=True)
        if not text:
            continue
            
        if "?" in text and len(text.split()) <= 25:
            current_question = text
        elif current_question and len(text.split()) >= 5:
            qa_pairs.append({
                "question": current_question,
                "answer": text[:1000],
                "source": url
            })
            current_question = None
    
    return qa_pairs

# --------------------------------
# Budget-Optimized Pipeline
# --------------------------------
def run_budget_optimized_pipeline():
    OUTPUT_DIR = Path(__file__).resolve().parent / "output_new"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Calculate optimal distribution
    total_roles = len(ROLE_TECH_MAP)
    total_skills = sum(len(skills) for skills in ROLE_TECH_MAP.values())
    searches_per_role = max(1, 250 // total_roles)  # ~12 searches per role
    
    logging.info(f"🎯 Budget Optimization:")
    logging.info(f"   Total Budget: 250 searches")
    logging.info(f"   Total Roles: {total_roles}")
    logging.info(f"   Total Skills: {total_skills}")
    logging.info(f"   Searches per Role: {searches_per_role}")
    
    # Create summary file to track progress
    summary = {
        "search_budget": {
            "total_budget": 250,
            "used": 0,
            "remaining": 250,
            "searches_per_role": searches_per_role
        },
        "total_roles": total_roles,
        "roles_processed": [],
        "total_qa_pairs": 0,
        "failed_searches": []
    }

    for role_idx, (role, skills) in enumerate(ROLE_TECH_MAP.items(), 1):
        if not search_budget.can_search():
            logging.warning(f"❌ Budget exhausted at role {role_idx}! Stopping.")
            break
            
        role_filename = role.replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '')
        out_path = OUTPUT_DIR / f"{role_filename}.json"
        
        # Load existing data if any
        existing_qa = []
        existing_skills = set()
        if out_path.exists():
            with open(out_path, "r", encoding="utf-8") as f:
                existing_qa = json.load(f)
            for qa in existing_qa:
                if "skill" in qa:
                    existing_skills.add(qa["skill"])
            logging.info(f"  📂 Loaded existing JSON for {role}: {len(existing_qa)} Q&A pairs, {len(existing_skills)} skills covered")
        else:
            logging.info(f"  📂 No existing JSON for {role}, starting fresh")
        
        # Determine skills to process: those not in existing_skills
        remaining_skills = [skill for skill in skills if skill not in existing_skills]
        
        role_results: List[Dict[str, Any]] = []  # New results to append
        logging.info(f"🔍 [{role_idx}/{total_roles}] Processing role: {role} | {search_budget.get_status()}")
        
        # Calculate how many skills we can afford to search for this role
        role_budget = min(searches_per_role, search_budget.remaining, len(remaining_skills))
        
        # Take up to role_budget from remaining_skills
        priority_skills = remaining_skills[:role_budget]
        
        logging.info(f"  📋 Will process {len(priority_skills)}/{len(remaining_skills)} remaining skills for this role (total skills: {len(skills)})")
        
        role_summary = {
            "role": role,
            "total_skills": len(skills),
            "existing_skills": len(existing_skills),
            "remaining_skills": len(remaining_skills),
            "skills_planned": len(priority_skills),
            "skills_processed": 0,
            "qa_pairs_found": 0,
            "searches_used": 0
        }

        for skill_idx, skill in enumerate(priority_skills, 1):
            if not search_budget.can_search():
                logging.warning(f"  ❌ Budget exhausted at skill {skill_idx}!")
                break
                
            logging.info(f"  📚 [{skill_idx}/{len(priority_skills)}] Processing skill: {skill}")
            
            # Single optimized search per skill to maximize coverage
            # Alternate between two search strategies for variety
            if skill_idx % 2 == 1:
                # Odd skills: Direct search
                query = f"{skill} interview questions site:geeksforgeeks.org OR site:interviewbit.com OR site:simplilearn.com"
            else:
                # Even skills: Role-specific search  
                query = f"{role} {skill} interview questions"
            
            urls = smart_search_for_skill(role, skill)
            
            logging.info(f"    📄 Found {len(urls)} URLs, scraping...")
            skill_qa_count = 0
            
            # Process URLs for this skill
            for url_idx, url in enumerate(urls, 1):
                try:
                    logging.info(f"      🌐 [{url_idx}/{len(urls)}] Scraping: {url[:60]}...")
                    qa_pairs = extract_qa_from_url(url)
                    
                    if qa_pairs:
                        for qa in qa_pairs:
                            qa["role"] = role
                            qa["skill"] = skill
                            qa["search_strategy"] = "direct" if skill_idx % 2 == 1 else "role_specific"
                        
                        role_results.extend(qa_pairs)
                        skill_qa_count += len(qa_pairs)
                        logging.info(f"        ✅ Found {len(qa_pairs)} Q&A pairs")
                    else:
                        logging.info(f"        ⚠️ No Q&A found")
                        
                except Exception as e:
                    logging.error(f"        ❌ Failed to scrape {url}: {e}")
                    continue
                
                # Very brief pause between URL scraping
                time.sleep(0.2)
            
            logging.info(f"  ✅ Skill '{skill}' completed: {skill_qa_count} Q&A pairs found")
            role_summary["skills_processed"] += 1
            role_summary["qa_pairs_found"] += skill_qa_count
            role_summary["searches_used"] += 1
            
            # Update summary with current search usage
            summary["search_budget"]["used"] = search_budget.used_searches
            summary["search_budget"]["remaining"] = search_budget.remaining

        # Save role results by appending to existing
        if role_results:
            # Combine with existing
            all_results = existing_qa + role_results
            
            # Remove duplicates within role
            unique_results = []
            seen_qa = set()
            for qa in all_results:
                qa_signature = (qa["question"].lower().strip(), qa["answer"][:100].lower().strip())
                if qa_signature not in seen_qa:
                    seen_qa.add(qa_signature)
                    unique_results.append(qa)
            
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(unique_results, f, indent=2, ensure_ascii=False)
            
            logging.info(f"✅ Saved {len(unique_results)} unique Q&A for {role} (added {len(role_results)}) → {out_path}")
            role_summary["qa_pairs_found"] = len(role_results)  # New ones added
            summary["total_qa_pairs"] += len(role_results)
        else:
            logging.warning(f"⚠️ No new Q&A found for {role}")
        
        summary["roles_processed"].append(role_summary)
        
        # Save progress summary
        summary_path = OUTPUT_DIR / "scraping_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logging.info(f"📊 Role {role} completed. Total Q&A so far: {summary['total_qa_pairs']} | {search_budget.get_status()}")
        
        # Brief pause between roles
        time.sleep(1)

    # Final summary
    logging.info("🎯 Pipeline finished!")
    logging.info(f"📈 Final Stats:")
    logging.info(f"   {search_budget.get_status()}")
    logging.info(f"   Total Q&A Pairs: {summary['total_qa_pairs']}")
    logging.info(f"   Failed Searches: {len(summary['failed_searches'])}")
    
    # Save final summary with search budget details
    summary["completion_status"] = "completed"
    summary["search_budget"]["used"] = search_budget.used_searches
    summary["search_budget"]["remaining"] = search_budget.remaining
    summary["search_budget"]["efficiency"] = f"{summary['total_qa_pairs'] / max(1, search_budget.used_searches):.2f} Q&A per search"
    
    final_summary_path = OUTPUT_DIR / "final_summary.json"
    with open(final_summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logging.info(f"📋 Final summary saved to: {final_summary_path}")

if __name__ == "__main__":
    run_budget_optimized_pipeline()