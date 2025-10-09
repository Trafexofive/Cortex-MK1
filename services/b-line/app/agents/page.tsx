"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Bot, Play, Eye, RefreshCw, FileCode } from "lucide-react";
import { api } from "@/lib/api/client";

interface Agent {
  name: string;
  summary: string;
  author: string;
  state: string;
  version?: string;
  cognitive_engine?: {
    primary?: {
      provider?: string;
      model?: string;
    };
  };
  import?: {
    tools?: string[];
    agents?: string[];
    relics?: string[];
  };
}

export default function AgentsPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const data = await api.manifests.listAgents();
      setAgents(data || []);
    } catch (error) {
      console.error("Failed to load agents:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await fetch("http://localhost:8082/registry/sync", { method: "POST" });
      await loadAgents(); // Reload after sync
    } catch (error) {
      console.error("Sync failed:", error);
    } finally {
      setSyncing(false);
    }
  };

  const handleViewAgent = (name: string) => {
    router.push(`/agents/${encodeURIComponent(name)}`);
  };

  const stableAgents = agents.filter(a => a.state === "stable");
  const unstableAgents = agents.filter(a => a.state === "unstable");

  return (
    <div className="flex h-screen">
      <Sidebar />
      
      <div className="flex flex-1 flex-col">
        <Header />
        
        <main className="flex-1 overflow-y-auto bg-background p-6">
          <div className="space-y-6">
            {/* Page Header */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Agents</h1>
                <p className="text-muted-foreground">
                  Intelligent entities that orchestrate tools and workflows
                </p>
              </div>
              <Button 
                onClick={handleSync} 
                disabled={syncing}
                variant="outline"
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                {syncing ? 'Syncing...' : 'Sync Manifests'}
              </Button>
            </div>

            {/* Tabs */}
            <Tabs defaultValue="all" className="space-y-4">
              <TabsList>
                <TabsTrigger value="all">All Agents ({agents.length})</TabsTrigger>
                <TabsTrigger value="stable">Stable ({stableAgents.length})</TabsTrigger>
                <TabsTrigger value="unstable">Unstable ({unstableAgents.length})</TabsTrigger>
              </TabsList>

              <TabsContent value="all" className="space-y-4">
                {loading ? (
                  <div className="text-center py-12 text-muted-foreground">
                    <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
                    Loading agents...
                  </div>
                ) : agents.length === 0 ? (
                  <Card>
                    <CardContent className="flex flex-col items-center justify-center py-12">
                      <Bot className="h-12 w-12 text-muted-foreground mb-4" />
                      <p className="text-lg font-medium">No agents found</p>
                      <p className="text-sm text-muted-foreground mb-4">
                        Add agent manifests to /manifests/agents/ and sync
                      </p>
                      <Button onClick={handleSync} disabled={syncing}>
                        <RefreshCw className={`mr-2 h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
                        Sync Now
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {agents.map((agent) => (
                      <Card key={agent.name} className="hover:border-primary/50 transition-colors">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <Bot className="h-8 w-8 text-primary" />
                            <Badge variant={agent.state === "stable" ? "default" : "secondary"}>
                              {agent.state}
                            </Badge>
                          </div>
                          <CardTitle className="mt-4">{agent.name}</CardTitle>
                          <CardDescription className="line-clamp-2">
                            {agent.summary || "No description"}
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2 mb-4">
                            {agent.author && (
                              <div className="text-xs text-muted-foreground">
                                by {agent.author}
                              </div>
                            )}
                            {agent.cognitive_engine?.primary && (
                              <div className="text-xs text-muted-foreground">
                                {agent.cognitive_engine.primary.provider}/{agent.cognitive_engine.primary.model}
                              </div>
                            )}
                            {agent.import?.tools && agent.import.tools.length > 0 && (
                              <div className="text-xs text-muted-foreground">
                                {agent.import.tools.length} tool(s)
                              </div>
                            )}
                          </div>
                          <div className="flex gap-2">
                            <Button 
                              size="sm" 
                              className="flex-1"
                              onClick={() => handleViewAgent(agent.name)}
                            >
                              <Eye className="mr-2 h-3 w-3" />
                              View
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              disabled
                              title="Coming soon: Agent execution"
                            >
                              <Play className="h-3 w-3" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              disabled
                              title="Coming soon: Manifest editor"
                            >
                              <FileCode className="h-3 w-3" />
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="stable">
                {stableAgents.length === 0 ? (
                  <Card>
                    <CardContent className="py-12 text-center text-muted-foreground">
                      No stable agents found
                    </CardContent>
                  </Card>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {stableAgents.map((agent) => (
                      <Card key={agent.name} className="hover:border-primary/50 transition-colors">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <Bot className="h-8 w-8 text-primary" />
                            <Badge variant="default">{agent.state}</Badge>
                          </div>
                          <CardTitle className="mt-4">{agent.name}</CardTitle>
                          <CardDescription className="line-clamp-2">
                            {agent.summary || "No description"}
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <Button 
                            size="sm" 
                            className="w-full"
                            onClick={() => handleViewAgent(agent.name)}
                          >
                            <Eye className="mr-2 h-3 w-3" />
                            View Details
                          </Button>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="unstable">
                {unstableAgents.length === 0 ? (
                  <Card>
                    <CardContent className="py-12 text-center text-muted-foreground">
                      No unstable agents found
                    </CardContent>
                  </Card>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {unstableAgents.map((agent) => (
                      <Card key={agent.name} className="hover:border-primary/50 transition-colors">
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <Bot className="h-8 w-8 text-primary" />
                            <Badge variant="secondary">{agent.state}</Badge>
                          </div>
                          <CardTitle className="mt-4">{agent.name}</CardTitle>
                          <CardDescription className="line-clamp-2">
                            {agent.summary || "No description"}
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <Button 
                            size="sm" 
                            className="w-full"
                            onClick={() => handleViewAgent(agent.name)}
                          >
                            <Eye className="mr-2 h-3 w-3" />
                            View Details
                          </Button>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </div>
        </main>
      </div>
    </div>
  );
}
