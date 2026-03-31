import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useDeferredValue, useEffect, useMemo, useState } from "react";
import {
  networkingApi,
  type Contact,
  type ContactCreate,
} from "../api/networking";
import { toast } from "../components/ui/toastService";

const emptyContact: ContactCreate = {
  name: "",
  company: "",
  role: "",
  relationship_strength: 3,
  linkedin_url: "",
  email: "",
  notes: "",
};

export function useNetworkingContacts() {
  const queryClient = useQueryClient();
  const [selectedContactId, setSelectedContactId] = useState<string | null>(null);
  const [form, setForm] = useState<ContactCreate>({ ...emptyContact });
  const [searchValue, setSearchValue] = useState("");
  const [companyLookup, setCompanyLookup] = useState("");
  const [companyConnections, setCompanyConnections] = useState<Contact[]>([]);
  const deferredSearch = useDeferredValue(searchValue);

  const { data: contactsData, isLoading: loadingContacts } = useQuery({
    queryKey: ["networking", "contacts"],
    queryFn: () => networkingApi.listContacts().then((response) => response.data),
  });
  const contacts = useMemo(() => contactsData ?? [], [contactsData]);

  useEffect(() => {
    if (!contacts.length || !selectedContactId) {
      return;
    }

    const selected = contacts.find((contact) => contact.id === selectedContactId);
    if (!selected) {
      return;
    }

    setForm({
      name: selected.name,
      company: selected.company ?? "",
      role: selected.role ?? "",
      relationship_strength: selected.relationship_strength,
      linkedin_url: selected.linkedin_url ?? "",
      email: selected.email ?? "",
      notes: selected.notes ?? "",
    });
  }, [contacts, selectedContactId]);

  const filteredContacts = contacts.filter((contact) => {
      const query = deferredSearch.trim().toLowerCase();
      if (!query) return true;
      return [contact.name, contact.company, contact.role, contact.email]
        .filter(Boolean)
        .some((value) => value?.toLowerCase().includes(query));
    });

  const selectedContact = contacts.find((contact) => contact.id === selectedContactId) ?? null;

  const createContactMutation = useMutation({
    mutationFn: (payload: ContactCreate) =>
      networkingApi.createContact(payload).then((response) => response.data),
    onSuccess: (contact) => {
      toast("success", "Contact added");
      queryClient.invalidateQueries({ queryKey: ["networking", "contacts"] });
      setSelectedContactId(contact.id);
    },
    onError: () => toast("error", "Failed to add contact"),
  });

  const updateContactMutation = useMutation({
    mutationFn: (payload: ContactCreate) =>
      networkingApi.updateContact(selectedContactId!, payload).then((response) => response.data),
    onSuccess: () => {
      toast("success", "Contact updated");
      queryClient.invalidateQueries({ queryKey: ["networking", "contacts"] });
    },
    onError: () => toast("error", "Failed to update contact"),
  });

  const deleteContactMutation = useMutation({
    mutationFn: () => networkingApi.deleteContact(selectedContactId!),
    onSuccess: () => {
      toast("success", "Contact deleted");
      queryClient.invalidateQueries({ queryKey: ["networking", "contacts"] });
      setSelectedContactId(null);
      setForm({ ...emptyContact });
    },
    onError: () => toast("error", "Failed to delete contact"),
  });

  const connectionSearchMutation = useMutation({
    mutationFn: (company: string) => networkingApi.findConnections(company).then((response) => response.data),
    onSuccess: (results) => {
      setCompanyConnections(results);
    },
    onError: () => toast("error", "Failed to look up connections"),
  });

  const saveContact = () => {
    if (!form.name?.trim()) {
      toast("error", "Name is required");
      return;
    }

    const payload: ContactCreate = {
      name: form.name.trim(),
      company: form.company?.trim() || null,
      role: form.role?.trim() || null,
      relationship_strength: Number(form.relationship_strength ?? 3),
      linkedin_url: form.linkedin_url?.trim() || null,
      email: form.email?.trim() || null,
      notes: form.notes?.trim() || null,
    };

    if (selectedContactId) {
      updateContactMutation.mutate(payload);
      return;
    }

    createContactMutation.mutate(payload);
  };

  const resetForm = () => {
    setSelectedContactId(null);
    setForm({ ...emptyContact });
  };

  return {
    contacts,
    companyConnections,
    companyLookup,
    connectionSearchMutation,
    deleteContactMutation,
    filteredContacts,
    form,
    loadingContacts,
    resetForm,
    saveContact,
    searchValue,
    selectedContact,
    selectedContactId,
    setCompanyLookup,
    setForm,
    setSearchValue,
    setSelectedContactId,
  };
}
