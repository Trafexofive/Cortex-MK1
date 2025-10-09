"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Bot, Play, Edit, Trash2, Plus } from "lucide-react";
import { api } from "@/lib/api/client";

export default function AgentsPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

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
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Agent
              </Button>
            </div>

            {/* Tabs */}
            <Tabs defaultValue="all" className="space-y-4">
              <TabsList>
                <TabsTrigger value="all">All Agents</TabsTrigger>
                <TabsTrigger value="stable">Stable</TabsTrigger>
                <TabsTrigger value="unstable">Unstable</TabsTrigger>
              </TabsList>

              <TabsContent value="all" className="space-y-4">
                {loading ? (
                  <div className="text-center py-12 text-muted-foreground">
                    Loading agents...
                  </div>
                ) : agents.length === 0 ? (
                  <Card>
                    <CardContent className="flex flex-col items-center justify-center py-12">
                      <Bot className="h-12 w-12 text-muted-foreground mb-4" />
                      <p className="text-lg font-medium">No agents found</p>
                      <p className="text-sm text-muted-foreground mb-4">
                        Create your first agent to get started
                      </p>
                      <Button>
                        <Plus className="mr-2 h-4 w-4" />
                        Create Agent
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {agents.map((agent) => (
                      <Card key={agent.name}>
                        <CardHeader>
                          <div className="flex items-start justify-between">
                            <Bot className="h-8 w-8 text-primary" />
                            <Badge variant={agent.state === "stable" ? "default" : "secondary"}>
                              {agent.state}
                            </Badge>
                          </div>
                          <CardTitle className="mt-4">{agent.name}</CardTitle>
                          <CardDescription>{agent.summary}</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="flex gap-2">
                            <Button size="sm" className="flex-1">
                              <Play className="mr-2 h-3 w-3" />
                              Execute
                            </Button>
                            <Button size="sm" variant="outline">
                              <Edit className="h-3 w-3" />
                            </Button>
                            <Button size="sm" variant="outline">
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="stable">
                <Card>
                  <CardContent className="py-12 text-center text-muted-foreground">
                    Stable agents will appear here
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="unstable">
                <Card>
                  <CardContent className="py-12 text-center text-muted-foreground">
                    Unstable agents will appear here
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </main>
      </div>
    </div>
  );
}
