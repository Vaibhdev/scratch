import React, { useState, useEffect } from 'react';
import client from '../api/client';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, RefreshCw, ThumbsUp, ThumbsDown, MessageSquare, Wand2, Save } from 'lucide-react';

const Editor = () => {
    const { projectId } = useParams();
    const navigate = useNavigate();
    const [project, setProject] = useState(null);
    const [sections, setSections] = useState([]);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState({}); // Map of sectionId -> boolean
    const [refining, setRefining] = useState({}); // Map of sectionId -> boolean
    const [refinePrompts, setRefinePrompts] = useState({}); // Map of sectionId -> string

    useEffect(() => {
        fetchProjectData();
    }, [projectId]);

    const fetchProjectData = async () => {
        try {
            const projectRes = await client.get(`/projects/${projectId}`);
            setProject(projectRes.data);

            const sectionsRes = await client.get(`/documents/${projectRes.data.document.id}/sections`);
            setSections(sectionsRes.data);
        } catch (error) {
            console.error("Error fetching data:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerate = async (sectionId) => {
        setGenerating({ ...generating, [sectionId]: true });
        try {
            await client.post(`/documents/sections/${sectionId}/generate`);
            // Refresh sections to get new content
            const sectionsRes = await client.get(`/documents/${project.document.id}/sections`);
            setSections(sectionsRes.data);
        } catch (error) {
            console.error("Error generating content:", error);
            alert("Failed to generate content.");
        } finally {
            setGenerating({ ...generating, [sectionId]: false });
        }
    };

    const handleRefine = async (sectionId) => {
        const prompt = refinePrompts[sectionId];
        if (!prompt) return;

        setRefining({ ...refining, [sectionId]: true });
        try {
            await client.post(`/documents/sections/${sectionId}/refine?prompt=${encodeURIComponent(prompt)}`);
            // Refresh sections
            const sectionsRes = await client.get(`/documents/${project.document.id}/sections`);
            setSections(sectionsRes.data);
            setRefinePrompts({ ...refinePrompts, [sectionId]: '' });
        } catch (error) {
            console.error("Error refining content:", error);
            alert("Failed to refine content.");
        } finally {
            setRefining({ ...refining, [sectionId]: false });
        }
    };

    const handleExport = async () => {
        try {
            const response = await client.get(`/export/${project.document.id}`, {
                responseType: 'blob',
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `${project.title}.${project.document_type}`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            console.error("Error exporting:", error);
            alert("Failed to export document.");
        }
    };

    if (loading) return <div className="p-8 text-center">Loading...</div>;
    if (!project) return <div className="p-8 text-center">Project not found</div>;

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* Header */}
            <header className="bg-white shadow-sm p-4 flex justify-between items-center sticky top-0 z-10">
                <div className="flex items-center gap-4">
                    <button onClick={() => navigate('/dashboard')} className="text-gray-500 hover:text-gray-700">
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <h1 className="text-xl font-bold text-gray-800">{project.title}</h1>
                        <span className="text-xs text-gray-500 uppercase tracking-wider">{project.document_type}</span>
                    </div>
                </div>
                <button
                    onClick={handleExport}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-green-700 transition"
                >
                    <Download size={18} /> Export
                </button>
            </header>

            {/* Main Content */}
            <main className="flex-1 container mx-auto p-8 max-w-4xl">
                <div className="space-y-8">
                    {sections.map((section) => (
                        <div key={section.id} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                            {/* Section Header */}
                            <div className="bg-gray-50 p-4 border-b flex justify-between items-center">
                                <h3 className="font-semibold text-gray-700">
                                    <span className="text-gray-400 mr-2">#{section.order + 1}</span>
                                    {section.title}
                                </h3>
                                {!section.content && (
                                    <button
                                        onClick={() => handleGenerate(section.id)}
                                        disabled={generating[section.id]}
                                        className="text-blue-600 text-sm flex items-center gap-1 hover:underline disabled:opacity-50"
                                    >
                                        {generating[section.id] ? <RefreshCw className="animate-spin" size={14} /> : <Wand2 size={14} />}
                                        Generate Content
                                    </button>
                                )}
                            </div>

                            {/* Content Area */}
                            <div className="p-6">
                                {section.content ? (
                                    <div className="prose max-w-none mb-6">
                                        <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
                                            {section.content}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="text-center py-8 text-gray-400 italic bg-gray-50 rounded-lg border border-dashed">
                                        No content generated yet.
                                    </div>
                                )}

                                {/* Refinement Tools */}
                                {section.content && (
                                    <div className="mt-6 pt-6 border-t">
                                        <div className="flex gap-2 mb-4">
                                            <input
                                                type="text"
                                                placeholder="Refinement instruction (e.g., 'Make it shorter', 'Add more details')"
                                                className="flex-1 border p-2 rounded text-sm"
                                                value={refinePrompts[section.id] || ''}
                                                onChange={(e) => setRefinePrompts({ ...refinePrompts, [section.id]: e.target.value })}
                                            />
                                            <button
                                                onClick={() => handleRefine(section.id)}
                                                disabled={refining[section.id] || !refinePrompts[section.id]}
                                                className="bg-blue-100 text-blue-700 px-3 py-2 rounded text-sm font-medium hover:bg-blue-200 disabled:opacity-50"
                                            >
                                                {refining[section.id] ? 'Refining...' : 'Refine'}
                                            </button>
                                        </div>

                                        <div className="flex items-center justify-between text-gray-400 text-sm">
                                            <div className="flex gap-4">
                                                <button className="flex items-center gap-1 hover:text-green-500"><ThumbsUp size={16} /> Helpful</button>
                                                <button className="flex items-center gap-1 hover:text-red-500"><ThumbsDown size={16} /> Not Helpful</button>
                                            </div>
                                            <button className="flex items-center gap-1 hover:text-blue-500"><MessageSquare size={16} /> Add Comment</button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </main>
        </div>
    );
};

export default Editor;
