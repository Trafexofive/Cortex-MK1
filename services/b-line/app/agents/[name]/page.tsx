"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft, Bot, Cpu, RefreshCw, Wrench, Users, Server } from "lucide-react";
import { api } from "@/lib/api/client";

interface Agent {
  name: string;
  summary: string;
  author: string;
  state: string;
  version?: string;
  persona?: {
    agent?: string;
  };
  cognitive_engine?: {
    primary?: {
      provider?: string;
      model?: string;
      temperature?: number;
    };
    parameters?: Record<string, any>;
  };
  import?: {
    tools?: string[];
    agents?: string[];
    relics?: string[];
  };
  environment?: {
    variables?: Record<string, string>;
  };
}

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.name) {
      loadAgent(params.name as string);
    }
  }, [params.name]);

  const loadAgent = async (name: string) => {
    try {
      const data = await api.manifests.getAgent(name);
      setAgent(data);
    } catch (error) {
      console.error("Failed to load agent:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold">Agent not found</h2>
          <Button className="mt-4" onClick={() => router.push("/agents")}>
            Back to Agents
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <Sidebar />
      
      <div className="flex flex-1 flex-col">
        <Header />
        
        <main className="flex-1 overflow-y-auto bg-background p-6">
          <div className="max-w-5xl mx-auto space-y-6">
            {/* Back Button */}
            <Button variant="ghost" onClick={() => router.push("/agents")}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Agents
            </Button>

            {/* Agent Header */}
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <Bot className="h-10 w-10 text-primary" />
                  <div>
                    <h1 className="text-3xl font-bold tracking-tight">{agent.name}</h1>
                    {agent.version && (
                      <p className="text-sm text-muted-foreground">v{agent.version}</p>
                    )}
                  </div>
                </div>
                <p className="text-lg text-muted-foreground">{agent.summary}</p>
              </div>
              <div className="flex gap-2">
                <Badge variant={agent.state === "stable" ? "default" : "secondary"} className="text-sm">
                  {agent.state}
                </Badge>
              </div>
            </div>

            <Separator />

            {/* Details Grid */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Basic Info */}
              <Card>
                <CardHeader>
                  <CardTitle>Basic Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <div className="text-sm font-medium">Author</div>
                    <div className="text-sm text-muted-foreground">{agent.author || "Unknown"}</div>
                  </div>
                  <div>
                    <div className="text-sm font-medium">State</div>
                    <div className="text-sm text-muted-foreground capitalize">{agent.state}</div>
                  </div>
                  {agent.version && (
                    <div>
                      <div className="text-sm font-medium">Version</div>
                      <div className="text-sm text-muted-foreground">{agent.version}</div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Cognitive Engine */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Cpu className="h-4 w-4" />
                    Cognitive Engine
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {agent.cognitive_engine?.primary ? (
                    <>
                      <div>
                        <div className="text-sm font-medium">Provider</div>
                        <div className="text-sm text-muted-foreground capitalize">
                          {agent.cognitive_engine.primary.provider || "Not specified"}
                        </div>
                      </div>
                      <div>
                        <div className="text-sm font-medium">Model</div>
                        <div className="text-sm text-muted-foreground">
                          {agent.cognitive_engine.primary.model || "Not specified"}
                        </div>
                      </div>
                      {agent.cognitive_engine.primary.temperature !== undefined && (
                        <div>
                          <div className="text-sm font-medium">Temperature</div>
                          <div className="text-sm text-muted-foreground">
                            {agent.cognitive_engine.primary.temperature}
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-sm text-muted-foreground">No cognitive engine configured</div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Imports */}
            {agent.import && (Object.keys(agent.import).length > 0) && (
              <Card>
                <CardHeader>
                  <CardTitle>Imported Resources</CardTitle>
                  <CardDescription>
                    Tools, agents, and relics this agent depends on
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {agent.import.tools && agent.import.tools.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Wrench className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Tools ({agent.import.tools.length})</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {agent.import.tools.map((tool) => (
                          <Badge key={tool} variant="outline">{tool}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {agent.import.agents && agent.import.agents.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Agents ({agent.import.agents.length})</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {agent.import.agents.map((agentName) => (
                          <Badge key={agentName} variant="outline">{agentName}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {agent.import.relics && agent.import.relics.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Server className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Relics ({agent.import.relics.length})</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {agent.import.relics.map((relic) => (
                          <Badge key={relic} variant="outline">{relic}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Persona */}
            {agent.persona?.agent && (
              <Card>
                <CardHeader>
                  <CardTitle>Persona</CardTitle>
                  <CardDescription>Agent's behavioral configuration</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-sm text-muted-foreground font-mono">
                    {agent.persona.agent}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Environment Variables */}
            {agent.environment?.variables && Object.keys(agent.environment.variables).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Environment Variables</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(agent.environment.variables).map(([key, value]) => (
                      <div key={key} className="flex justify-between text-sm">
                        <span className="font-mono text-muted-foreground">{key}</span>
                        <span className="font-mono">{value}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="flex gap-2">
                <Button disabled title="Coming soon: Agent execution with streaming">
                  Execute Agent
                </Button>
                <Button variant="outline" disabled title="Coming soon: Manifest editor">
                  Edit Manifest
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => loadAgent(agent.name)}
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
