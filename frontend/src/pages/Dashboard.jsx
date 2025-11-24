import React, { useState, useEffect } from 'react';
import client from '../api/client';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Plus, FileText, Monitor } from 'lucide-react';

const Dashboard = () => {
    const [projects, setProjects] = useState([]);
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        try {
            const response = await client.get('/projects/');
            setProjects(response.data);
        } catch (error) {
            console.error("Error fetching projects:", error);
        }
    };

    const handleCreateProject = () => {
        navigate('/create-project');
    };

    const handleDelete = async (id) => {
        if (window.confirm("Are you sure you want to delete this project?")) {
            try {
                await client.delete(`/projects/${id}`);
                fetchProjects();
            } catch (error) {
                console.error("Error deleting project:", error);
            }
        }
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <nav className="bg-white shadow-sm p-4 flex justify-between items-center">
                <h1 className="text-xl font-bold text-gray-800">Generation Platform</h1>
                <div className="flex items-center gap-4">
                    <span className="text-gray-600">{user?.email}</span>
                    <button onClick={logout} className="text-red-500 hover:text-red-700">Logout</button>
                </div>
            </nav>

            <main className="container mx-auto p-8">
                <div className="flex justify-between items-center mb-8">
                    <h2 className="text-2xl font-bold text-gray-800">My Projects</h2>
                    <button
                        onClick={handleCreateProject}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700 transition"
                    >
                        <Plus size={20} /> New Project
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {projects.map((project) => (
                        <div key={project.id} className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition border border-gray-100">
                            <div className="flex justify-between items-start mb-4">
                                <div className={`p-3 rounded-lg ${project.document_type === 'docx' ? 'bg-blue-100 text-blue-600' : 'bg-orange-100 text-orange-600'}`}>
                                    {project.document_type === 'docx' ? <FileText size={24} /> : <Monitor size={24} />}
                                </div>
                                <button onClick={() => handleDelete(project.id)} className="text-gray-400 hover:text-red-500">
                                    &times;
                                </button>
                            </div>
                            <h3 className="text-lg font-semibold text-gray-800 mb-2">{project.title}</h3>
                            <p className="text-gray-500 text-sm mb-4 line-clamp-2">{project.description || "No description"}</p>
                            <div className="flex justify-between items-center text-sm text-gray-400">
                                <span>{new Date(project.created_at).toLocaleDateString()}</span>
                                <Link to={`/editor/${project.id}`} className="text-blue-600 hover:underline">
                                    Open Editor &rarr;
                                </Link>
                            </div>
                        </div>
                    ))}
                </div>

                {projects.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                        No projects yet. Create one to get started!
                    </div>
                )}
            </main>
        </div>
    );
};

export default Dashboard;
